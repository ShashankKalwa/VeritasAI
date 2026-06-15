"""
VeritasAI Ensemble Analysis Engine v4.0
Multi-engine weighted scoring with 6-label verdict taxonomy.

Verdict: CREDIBLE → MOSTLY_TRUE → MIXED → MOSTLY_FALSE → FALSE | INSUFFICIENT_DATA
Weights: BERT=0.35, Heuristic=0.30, GoogleFC=0.25 (ClaimBuster excluded from verdict)
"""
import re
import time
import logging
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, field_validator
from lib.heuristics import heuristic_analyze
from lib.ml_model import get_hf_detector, get_claimbuster_hf, get_google_factcheck
from lib.file_parser import extract_text, is_meaningful_content
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "text", "md"}

# ─────────────────────────────────────────────────────────
# ENGINE WEIGHTS (FIX-001)
# ClaimBuster is NOT included — it only measures check-worthiness
# ─────────────────────────────────────────────────────────
ENGINE_WEIGHTS = {
    "bert_huggingface": 0.35,
    "heuristic_nlp": 0.30,
    "google_fact_check": 0.25,
}

ENGINE_META = {
    "bert_huggingface": {"name": "HuggingFace BERT", "color": "#6366f1"},
    "heuristic_nlp": {"name": "Heuristic NLP", "color": "#f59e0b"},
    "claimbuster_deberta": {"name": "ClaimBuster DeBERTa", "color": "#8b5cf6"},
    "google_fact_check": {"name": "Google Fact Check", "color": "#10b981"},
}

# Display order for engines (FIX-002)
ENGINE_ORDER = ["bert_huggingface", "heuristic_nlp", "claimbuster_deberta", "google_fact_check"]


# ─────────────────────────────────────────────────────────
# VERDICT MAPPING (FIX-001)
# Score is 0-1 scale where 0=false, 1=credible
# ─────────────────────────────────────────────────────────

def map_score_to_verdict(score: float) -> str:
    """Map 0-1 credibility score to verdict label."""
    if score < 0.35:
        return "INSUFFICIENT_DATA"
    elif score < 0.45:
        return "FALSE"
    elif score < 0.55:
        return "MOSTLY_FALSE"
    elif score < 0.65:
        return "MIXED"
    elif score < 0.80:
        return "MOSTLY_TRUE"
    else:
        return "CREDIBLE"


def get_confidence_tier(confidence_pct: int) -> str:
    if confidence_pct < 55:
        return "LOW"
    elif confidence_pct < 75:
        return "MEDIUM"
    else:
        return "HIGH"


# ─────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        v = re.sub(r"<[^>]*>", "", v).strip()
        if len(v) < 10:
            raise ValueError("Text must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Text must be under 5000 characters")
        return v


# ─────────────────────────────────────────────────────────
# SAFE ENGINE CALLS
# ─────────────────────────────────────────────────────────

async def _safe_hf(text):
    try:
        return await asyncio.wait_for(get_hf_detector().predict(text), timeout=5.0)
    except Exception as e:
        logger.warning(f"HF engine: {e}")
        return None


async def _safe_cb(text):
    try:
        return await asyncio.wait_for(get_claimbuster_hf().check(text), timeout=5.0)
    except Exception as e:
        logger.warning(f"ClaimBuster engine: {e}")
        return None


async def _safe_gfc(text):
    try:
        return await asyncio.wait_for(get_google_factcheck().check(text), timeout=3.0)
    except Exception as e:
        logger.warning(f"Google FC engine: {e}")
        return None


# ─────────────────────────────────────────────────────────
# ANALYSIS SUMMARY GENERATION
# ─────────────────────────────────────────────────────────

def generate_analysis_summary(
    verdict: str, confidence_pct: int, engines_active: int,
    primary_issue: dict | None, gfc_matches: int, content_type_label: str
) -> str:
    """Generate a human-readable analysis summary."""
    issue_text = ""
    if primary_issue:
        issue_text = f" Primary concern: {primary_issue['label'].lower()}."

    gfc_text = ""
    if gfc_matches > 0:
        gfc_text = f" Google Fact Check found {gfc_matches} matching verified claim{'s' if gfc_matches > 1 else ''}."

    if verdict == "INSUFFICIENT_DATA":
        return (
            f"Insufficient signals to make a reliable determination. "
            f"Only {engines_active} engine{'s' if engines_active != 1 else ''} returned results. "
            f"Submit more context or a longer text for better analysis."
        )

    if verdict in ("FALSE", "MOSTLY_FALSE"):
        return (
            f"Ensemble of {engines_active} engines detected misinformation signals "
            f"with {confidence_pct}% confidence.{issue_text}{gfc_text}"
        )
    elif verdict == "MIXED":
        return (
            f"Ensemble of {engines_active} engines found mixed signals — content contains "
            f"both credible and questionable elements ({confidence_pct}% confidence).{issue_text}{gfc_text}"
        )
    else:  # CREDIBLE, MOSTLY_TRUE
        ct_note = ""
        if content_type_label == "Opinion / Satire":
            ct_note = " Note: Opinion and satire content is scored differently from factual reporting."
        return (
            f"Multi-engine verification ({engines_active} engines) confirms largely credible "
            f"reporting with {confidence_pct}% confidence.{issue_text}{gfc_text}{ct_note}"
        )


# ─────────────────────────────────────────────────────────
# CORE ENSEMBLE LOGIC (FIX-001)
# ─────────────────────────────────────────────────────────

async def run_ensemble(text: str, source_type: str = "text") -> dict:
    """
    Core ensemble detection. All engines run in parallel.
    ClaimBuster is separated — it only contributes check-worthiness, NOT verdict.
    """
    start_time = time.time()

    # ── Engine 1: Heuristic NLP (instant, always available) ──
    h = heuristic_analyze(text)
    if not h:
        raise HTTPException(400, "Text too short for analysis")

    content_type = h["content_type"]
    category = h["category"]

    # ── Engines 2-4: Run ALL in parallel ──
    hf_result, cb_result, gfc_result = await asyncio.gather(
        _safe_hf(text), _safe_cb(text), _safe_gfc(text)
    )

    # ── Build engine status array (FIX-002 — always show all 4) ──
    engines = []
    engine_scores = {}  # For weighted average: engine_id -> 0-1 score (0=false, 1=credible)

    # --- BERT ---
    bert_entry = {
        "name": "HuggingFace BERT",
        "id": "bert_huggingface",
        "status": "unavailable",
        "verdict": None,
        "score": None,
        "color": "#6366f1",
    }
    if hf_result:
        # HF returns verdict=FAKE/REAL, confidence=0-100
        # Convert: REAL=high score, FAKE=low score
        if hf_result["verdict"] == "REAL":
            bert_score_01 = hf_result["confidence"] / 100.0
        else:
            bert_score_01 = 1.0 - (hf_result["confidence"] / 100.0)
        bert_entry["status"] = "active"
        bert_entry["verdict"] = "CREDIBLE" if hf_result["verdict"] == "REAL" else "FALSE"
        bert_entry["score"] = round(bert_score_01, 4)
        engine_scores["bert_huggingface"] = bert_score_01
    engines.append(bert_entry)

    # --- Heuristic NLP ---
    heur_entry = {
        "name": "Heuristic NLP",
        "id": "heuristic_nlp",
        "status": "active",  # Always active
        "verdict": h["verdict"],
        "score": round(h["heuristic_score_01"], 4),
        "flags_count": h["false_flag_count"] + h["credible_flag_count"],
        "color": "#f59e0b",
    }
    engine_scores["heuristic_nlp"] = h["heuristic_score_01"]
    engines.append(heur_entry)

    # --- ClaimBuster (check-worthiness ONLY — NOT included in verdict score) ---
    cb_entry = {
        "name": "ClaimBuster DeBERTa",
        "id": "claimbuster_deberta",
        "status": "unavailable",
        "check_worthiness": None,
        "color": "#8b5cf6",
    }
    cb_score_raw = None
    cb_checkworthy = None
    if cb_result:
        cb_entry["status"] = "active"
        cb_entry["check_worthiness"] = round(cb_result["cfs_score"], 4)
        cb_score_raw = cb_result["cfs_score"]
        cb_checkworthy = cb_result["is_checkworthy"]
    engines.append(cb_entry)

    # --- Google Fact Check ---
    gfc_entry = {
        "name": "Google Fact Check",
        "id": "google_fact_check",
        "status": "unavailable",
        "matches_found": 0,
        "top_match": None,
        "color": "#10b981",
    }
    gfc_found = False
    gfc_matches = 0
    gfc_claims_list = []
    if gfc_result:
        gfc_entry["status"] = "active"
        gfc_found = gfc_result.get("found", False)
        gfc_claims_list = gfc_result.get("claims", [])[:3]
        gfc_matches = len(gfc_claims_list) if gfc_found else 0
        gfc_entry["matches_found"] = gfc_matches

        if gfc_found and gfc_claims_list:
            gfc_entry["top_match"] = {
                "claim": gfc_claims_list[0].get("text", ""),
                "rating": gfc_claims_list[0].get("rating", "Unknown"),
                "source": gfc_claims_list[0].get("publisher", "Unknown"),
                "url": gfc_claims_list[0].get("url", ""),
            }

        # Convert GFC overall rating to score
        overall = gfc_result.get("overall_rating")
        if overall == "DEBUNKED":
            engine_scores["google_fact_check"] = 0.15  # Strongly false
        elif overall == "VERIFIED":
            engine_scores["google_fact_check"] = 0.90  # Strongly credible
        elif overall == "MIXED":
            engine_scores["google_fact_check"] = 0.55  # Ambiguous
        elif gfc_found:
            engine_scores["google_fact_check"] = 0.50  # Found but no clear rating
        # If not found, don't add to engine_scores → weight redistributed
    engines.append(gfc_entry)

    # ── WEIGHTED AVERAGE CALCULATION (FIX-001) ──
    active_engines = [eid for eid in engine_scores.keys()]
    active_count = len(active_engines)

    if active_count < 2:
        # INSUFFICIENT DATA — too few engines
        confidence_pct = max(round(
            sum(engine_scores.values()) / max(len(engine_scores), 1) * 100
        ), 1)
        confidence_pct = min(confidence_pct, 34)  # Cap at 34%

        verdict_label = "INSUFFICIENT_DATA"
        weighted_score = sum(engine_scores.values()) / max(len(engine_scores), 1)
    else:
        # Calculate weighted average with weight redistribution
        total_weight = sum(ENGINE_WEIGHTS.get(eid, 0) for eid in active_engines)
        if total_weight == 0:
            total_weight = 1.0

        weighted_score = sum(
            engine_scores[eid] * (ENGINE_WEIGHTS.get(eid, 0) / total_weight)
            for eid in active_engines
        )

        # Map to verdict
        verdict_label = map_score_to_verdict(weighted_score)

        # Confidence = how far the score is from the nearest threshold boundary
        # Expressed as percentage (50-99)
        distance_from_center = abs(weighted_score - 0.5)
        confidence_pct = min(round(50 + distance_from_center * 100), 99)

        # Apply agreement bonus/penalty
        engine_verdicts_set = set()
        for eid in active_engines:
            s = engine_scores[eid]
            if s >= 0.65:
                engine_verdicts_set.add("positive")
            elif s <= 0.45:
                engine_verdicts_set.add("negative")
            else:
                engine_verdicts_set.add("mixed")

        if len(engine_verdicts_set) == 1:
            # Perfect agreement — boost confidence
            confidence_pct = min(confidence_pct + 8, 99)
        elif len(engine_verdicts_set) >= 3:
            # Major disagreement — cap confidence
            confidence_pct = min(confidence_pct, 65)

        # Ensure minimum confidence above INSUFFICIENT_DATA threshold
        if verdict_label != "INSUFFICIENT_DATA":
            confidence_pct = max(confidence_pct, 35)

    confidence_tier = get_confidence_tier(confidence_pct)

    # ── STRUCTURED INDICATORS (FIX-004) ──
    structured_indicators = h["structured_indicators"]

    # Add Google FC contradiction indicator if applicable
    if gfc_found and gfc_result.get("overall_rating") == "DEBUNKED":
        structured_indicators["primary_issue"] = {
            "id": "FC_CONTRADICT",
            "label": "Contradicted by Fact Checks",
            "description": f"Google Fact Check found {gfc_matches} matching claim(s) rated FALSE",
        }
        # Move original primary to secondary
        if h["structured_indicators"]["primary_issue"]["id"] != "NO_RED_FLAGS":
            existing = h["structured_indicators"]["primary_issue"]
            structured_indicators["secondary_issues"] = [
                {"id": existing["id"], "label": existing["label"]},
            ] + structured_indicators.get("secondary_issues", [])[:1]

    # Add ClaimBuster unsupported claim indicator
    if cb_checkworthy and cb_score_raw and cb_score_raw > 0.7 and not gfc_found:
        if structured_indicators.get("secondary_issues") is not None:
            structured_indicators["secondary_issues"].append({
                "id": "UNSUPPORTED",
                "label": "Unsupported Claim",
            })
            structured_indicators["secondary_issues"] = structured_indicators["secondary_issues"][:2]

    # Legacy indicator labels
    indicator_labels = h["indicators"]

    # ── CLAIM ANALYSIS (FIX-005) ──
    claim_analysis = None
    if cb_score_raw is not None:
        cw_label = "Needs Verification" if cb_checkworthy else "Low Priority"
        claim_analysis = {
            "check_worthiness_score": round(cb_score_raw, 4),
            "check_worthiness_pct": round(cb_score_raw * 100, 1),
            "label": cw_label,
        }

    # ── FACT CHECK SECTION (FIX-005) ──
    fact_check = None
    if gfc_found:
        fact_check = {
            "matches_found": gfc_matches,
            "results": [
                {
                    "claim": cl.get("text", ""),
                    "rating": cl.get("rating", "Unknown"),
                    "publisher": cl.get("publisher", "Unknown"),
                    "url": cl.get("url", ""),
                }
                for cl in gfc_claims_list
            ],
        }

    # ── ANALYSIS SUMMARY ──
    analysis_summary = generate_analysis_summary(
        verdict_label, confidence_pct, active_count,
        structured_indicators.get("primary_issue"),
        gfc_matches, content_type.get("label", "News Report"),
    )

    elapsed_ms = round((time.time() - start_time) * 1000)

    # ── META (FIX-005) ──
    signals_detected = h["false_flag_count"] + h["credible_flag_count"]
    meta = {
        "engines_used": active_count,
        "engines_total": 4,
        "input_type": source_type,
        "signals_detected": signals_detected,
        "analysis_time_ms": elapsed_ms,
    }

    # ── Fire-and-forget Supabase store ──
    async def _store():
        try:
            sb = get_supabase()
            sb.table("analyses").insert({
                "input_text": text[:500],
                "verdict": verdict_label,
                "confidence": confidence_pct,
                "analysis": analysis_summary,
                "indicators": indicator_labels,
                "category": category,
                "heuristic_score": h["heuristic_score"],
                "is_public": True,
            }).execute()
        except Exception as e:
            logger.error(f"Supabase error: {e}")

    asyncio.create_task(_store())

    # ── BUILD FINAL RESPONSE (FIX-005 full schema) ──
    return {
        "verdict": {
            "label": verdict_label,
            "confidence": round(weighted_score, 4),
            "confidence_pct": confidence_pct,
            "confidence_tier": confidence_tier,
        },
        "content_type": content_type,
        "engines": engines,
        "analysis_summary": analysis_summary,
        "indicators": structured_indicators,
        "fact_check": fact_check,
        "claim_analysis": claim_analysis,
        "category": category,
        "meta": meta,

        # Legacy flat fields for backward compat
        "verdict_label": verdict_label,
        "confidence_pct": confidence_pct,
        "heuristic_score": h["heuristic_score"],
        "indicator_labels": indicator_labels,
    }


# ─────────────────────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────────────────────

@router.post("/api/analyze")
async def analyze_text(req: AnalyzeRequest):
    """Analyze text for fake news using multi-engine ensemble."""
    return await run_ensemble(req.text, "text")


@router.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    """Upload PDF, DOCX, or TXT for fake news analysis."""
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

    is_valid, reason = is_meaningful_content(text)
    if not is_valid:
        raise HTTPException(422, reason)

    return await run_ensemble(text[:5000].strip(), f"file:{ext}")
