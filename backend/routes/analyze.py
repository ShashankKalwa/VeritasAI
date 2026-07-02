"""
VeritasAI v2 — Ensemble Analysis Engine
Retrieval-augmented claim-level verification pipeline.

Pipeline: Input → Claims → ClaimBuster Gate → Evidence → Credibility →
          BERT+Heuristic → LLM Reasoning → Ensemble Verdict → Explainability
"""
import os
import re
import logging
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File, Request, Depends
from pydantic import BaseModel, field_validator
from lib.file_parser import extract_text, is_meaningful_content
from lib.supabase_client import get_supabase
from lib.limiter import limiter
from lib.daily_quota import check_daily_quota

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "text", "md"}
CLAIMBUSTER_GATE_THRESHOLD = int(os.getenv("CLAIMBUSTER_GATE_THRESHOLD", "40"))
PIPELINE_TIMEOUT = 55  # seconds (increased to prevent first-time timeouts)


class AnalyzeRequest(BaseModel):
    text: str = ""
    input_type: str = "text"       # url | text | headline | social_post
    content_type: str = "auto"     # auto | news_report | opinion_satire | social_media_post

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        v = re.sub(r"<[^>]*>", "", v).strip()
        if len(v) < 10:
            raise ValueError("Text must be at least 10 characters")
        if len(v) > 10000:
            raise ValueError("Text must be under 10000 characters")
        return v


async def run_v2_pipeline(text: str, input_type: str = "text", content_type: str = "auto", source_type: str = "text") -> dict:
    """
    Core v2 pipeline orchestrator. Implements the 12-step pipeline with:
    - Error isolation per claim (failure in one claim doesn't crash others)
    - Timeout budget (25s total, partial results on timeout)
    - Parallel execution where possible
    """
    from lib.input_handler import normalize
    from lib.claim_extractor import extract_claims
    from lib.ml_model import claimbuster_score_async, bert_signal_async
    from lib.heuristics import manipulation_signal_async
    from lib.evidence_retriever import retrieve_evidence, retrieve_factcheck, aggregate_evidence
    from lib.source_credibility import score_evidence
    from lib.evidence_reasoner import reason
    from lib.ensemble_verdict_v2 import compute_claim_verdict, compute_overall_verdict
    from lib.explainability_formatter import format_response

    try:
        # Step 1-2: Input normalization
        normalized = await normalize(text, input_type, content_type)
        article_text = normalized["text"]
        detected_content_type = normalized["content_type"]

        if not article_text or len(article_text.strip()) < 10:
            raise HTTPException(400, "Could not extract meaningful text from input.")

        # Step 3: Claim extraction (LLM)
        claims = await asyncio.wait_for(
            extract_claims(article_text, detected_content_type),
            timeout=12.0,
        )

        if not claims:
            return format_response(
                claims=[],
                overall_verdict="Insufficient Evidence",
                overall_confidence=None,
                content_type=detected_content_type,
                text=article_text,
            )

        # Step 9: Run BERT + Heuristic in parallel (on full article text)
        # These are independent of per-claim processing
        bert_task = bert_signal_async(article_text)
        manip_task = manipulation_signal_async(article_text)
        bert_sig, manip_sig = await asyncio.gather(bert_task, manip_task)

        # Steps 4-10: Process each claim (with error isolation)
        async def process_claim(claim: dict) -> dict:
            """Process a single claim through the pipeline. Never raises."""
            claim_text = claim.get("claim_text", "")
            try:
                # Step 4: ClaimBuster gate
                cb_score = await claimbuster_score_async(claim_text)
                claim["claimbuster_score"] = cb_score
                claim["bert_signal"] = bert_sig
                claim["manipulation_signal"] = manip_sig

                if cb_score < CLAIMBUSTER_GATE_THRESHOLD:
                    # Skip evidence retrieval for non-checkworthy claims
                    claim["check_worthy"] = False
                    claim["verdict"] = "Opinion / Not Fact-Checkable"
                    claim["confidence"] = None
                    claim["final_score"] = 0.0
                    claim["reasoning"] = {
                        "supporting_evidence": [],
                        "contradicting_evidence": [],
                        "unclear_evidence": [],
                        "reasoning": f"ClaimBuster score ({cb_score:.0f}%) below threshold — "
                                     f"classified as opinion or non-factual statement.",
                        "google_factcheck_match": False,
                        "google_factcheck_details": None,
                    }
                    return claim

                claim["check_worthy"] = True

                # Steps 5-7: Evidence retrieval (search + fact check + aggregate)
                search_task = retrieve_evidence(claim_text)
                fc_task = retrieve_factcheck(claim_text)
                search_results, fc_results = await asyncio.gather(
                    search_task, fc_task
                )

                # Step 7: Aggregate
                evidence = aggregate_evidence(search_results, fc_results)

                # Step 8: Source credibility scoring
                evidence = score_evidence(evidence)

                # Step 10: Evidence reasoning (LLM)
                reasoning_result = await reason(
                    claim_text, evidence, bert_sig, manip_sig
                )
                claim["reasoning"] = reasoning_result

                # Step 11: Ensemble verdict
                verdict_result = compute_claim_verdict(
                    reasoning=reasoning_result,
                    bert_signal=bert_sig,
                    manipulation_signal=manip_sig,
                    google_factcheck_match=reasoning_result.get("google_factcheck_match", False),
                )
                claim["verdict"] = verdict_result["verdict"]
                claim["confidence"] = verdict_result["confidence"]
                claim["final_score"] = verdict_result["final_score"]

                return claim

            except asyncio.TimeoutError:
                logger.warning(f"Claim processing timeout: {claim_text[:60]}...")
                claim["verdict"] = "Insufficient Evidence"
                claim["confidence"] = None
                claim["final_score"] = 0.0
                claim["check_worthy"] = True
                claim["reasoning"] = {
                    "supporting_evidence": [], "contradicting_evidence": [],
                    "unclear_evidence": [],
                    "reasoning": "Processing timed out for this claim.",
                    "google_factcheck_match": False, "google_factcheck_details": None,
                }
                return claim
            except Exception as e:
                logger.error(f"Claim processing error: {e}")
                claim["verdict"] = "Insufficient Evidence"
                claim["confidence"] = None
                claim["final_score"] = 0.0
                claim["check_worthy"] = True
                claim["reasoning"] = {
                    "supporting_evidence": [], "contradicting_evidence": [],
                    "unclear_evidence": [],
                    "reasoning": f"Error processing this claim: {str(e)[:100]}",
                    "google_factcheck_match": False, "google_factcheck_details": None,
                }
                return claim

        # Process all claims concurrently with timeout
        processed_claims = await asyncio.wait_for(
            asyncio.gather(*[process_claim(c) for c in claims]),
            timeout=PIPELINE_TIMEOUT,
        )

        # Step 11: Overall article verdict
        overall = compute_overall_verdict(processed_claims)

        # Step 12: Format response
        response = format_response(
            claims=processed_claims,
            overall_verdict=overall["overall_verdict"],
            overall_confidence=overall["overall_confidence"],
            content_type=detected_content_type,
            text=article_text,
        )

        # Fire-and-forget Supabase store (legacy analyses table)
        _store_analysis(article_text, response, source_type)

        # Fire-and-forget: store in analyzed_news + trending_claims (Phase 8)
        async def _store_feed():
            try:
                from lib.feed_manager import store_analysis as feed_store
                await feed_store(
                    pipeline_result=response,
                    source="user_submitted",
                    headline=article_text[:200],
                )
            except Exception as e:
                logger.error(f"Feed store error: {e}")
        asyncio.create_task(_store_feed())

        return response

    except asyncio.TimeoutError:
        logger.warning("Pipeline timeout — returning partial results")
        # Return whatever we have
        return format_response(
            claims=[{
                "claim_id": "timeout",
                "claim_text": text[:200],
                "check_worthy": True,
                "verdict": "Insufficient Evidence",
                "confidence": None,
            }],
            overall_verdict="Insufficient Evidence",
            overall_confidence=None,
            content_type=content_type if content_type != "auto" else "news_report",
            text=text,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(500, f"Analysis pipeline error: {str(e)[:200]}")


def _store_analysis(text: str, response: dict, source_type: str):
    """Fire-and-forget Supabase storage."""
    async def _do_store():
        try:
            sb = get_supabase()
            sb.table("analyses").insert({
                "input_text": text[:500],
                "verdict": response.get("overall_verdict", "Insufficient Evidence"),
                "confidence": response.get("overall_confidence") or 0,
                "analysis": response.get("explainability", {}).get("primary_signal", ""),
                "indicators": response.get("explainability", {}).get("secondary_signals", []),
                "category": "General",
                "heuristic_score": 0,
                "is_public": True,
                "overall_verdict": response.get("overall_verdict"),
                "overall_confidence": response.get("overall_confidence"),
                "content_type": response.get("content_type", "news_report"),
                "claim_count": len(response.get("claims", [])),
                "claims": response.get("claims"),
                "explainability": response.get("explainability"),
                "top_sources": response.get("explainability", {}).get("top_sources"),
            }).execute()
        except Exception as e:
            logger.error(f"Supabase store error: {e}")
    asyncio.create_task(_do_store())


@router.post("/api/analyze")
@limiter.limit("5/minute;200/day")
async def analyze_text(
    request: Request,
    req: AnalyzeRequest,
    _quota=Depends(check_daily_quota)
):
    """Analyze text for misinformation using v2 retrieval-augmented pipeline."""
    return await run_v2_pipeline(
        text=req.text,
        input_type=req.input_type,
        content_type=req.content_type,
        source_type="text",
    )


@router.post("/api/analyze/file")
@limiter.limit("5/minute;200/day")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    _quota=Depends(check_daily_quota)
):
    """Upload PDF, DOCX, or TXT for misinformation analysis."""
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Use PDF, DOCX, or TXT.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Maximum 5MB.")
    if not content:
        raise HTTPException(400, "File is empty.")

    text = extract_text(file.filename, content)
    if not text or not text.strip():
        raise HTTPException(400, "Could not extract text from this file.")

    is_valid, reason_msg = is_meaningful_content(text)
    if not is_valid:
        raise HTTPException(422, reason_msg)

    return await run_v2_pipeline(
        text=text[:5000].strip(),
        input_type="text",
        content_type="auto",
        source_type=f"file:{ext}",
    )
