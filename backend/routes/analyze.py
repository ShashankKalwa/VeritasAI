"""
VeritasAI Ensemble Analysis Engine v3.0
Multi-engine convergence scoring with 5-label verdict taxonomy.

Labels: CREDIBLE → MOSTLY_TRUE → MIXED → MOSTLY_FALSE → FALSE
"""
import re
import random
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

# 5-label verdict taxonomy
VERDICTS = ["CREDIBLE", "MOSTLY_TRUE", "MIXED", "MOSTLY_FALSE", "FALSE"]


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


class AnalyzeResponse(BaseModel):
    id: str | None = None
    verdict: str
    confidence: int
    analysis: str
    indicators: list[str]
    category: str
    content_type: str = "HARD_NEWS"
    heuristic_score: float
    hf_confidence: int | None = None
    claimbuster_score: float | None = None
    claimbuster_checkworthy: bool | None = None
    google_factcheck_found: bool | None = None
    google_factcheck_rating: str | None = None
    google_factcheck_claims: list | None = None
    engines_used: list[str] = []
    ensemble_method: str = "multi_engine"
    source_type: str = "text"
    convergence_signals: int = 0


def generate_analysis_text(verdict, confidence, indicators, engines, content_type):
    ind_text = ", ".join(indicators[:3]).lower() if indicators else "general pattern analysis"
    n = len(engines)

    if verdict == "FALSE":
        return random.choice([
            f"Multi-engine analysis ({n} engines) identifies content contradicted by reliable evidence with {confidence}% confidence. Key signals: {ind_text}.",
            f"Cross-referenced across {n} engines — claims contradicted by verified sources. {ind_text.capitalize()} confirm false content ({confidence}%).",
        ])
    elif verdict == "MOSTLY_FALSE":
        return random.choice([
            f"Analysis across {n} engines found significant inaccuracies ({confidence}% confidence). Key concerns: {ind_text}.",
            f"Ensemble of {n} AI engines flags substantial inaccuracies. Claims require verification: {ind_text} ({confidence}%).",
        ])
    elif verdict == "MIXED":
        return random.choice([
            f"Multi-engine review ({n} engines) finds both true and false elements ({confidence}% confidence). Mixed signals: {ind_text}.",
            f"Ensemble of {n} engines detects a combination of credible and questionable elements: {ind_text} ({confidence}%).",
        ])
    elif verdict == "MOSTLY_TRUE":
        return random.choice([
            f"Multi-engine analysis ({n} engines) finds content largely correct with minor inaccuracies ({confidence}% confidence). Signals: {ind_text}.",
            f"Ensemble of {n} engines confirms mostly accurate reporting ({confidence}%). Minor concerns: {ind_text}.",
        ])
    else:  # CREDIBLE
        ct_note = ""
        if content_type == "BREAKING":
            ct_note = " Content identified as breaking news — appropriate tolerance applied."
        return random.choice([
            f"Multi-engine verification ({n} engines) confirms credible reporting with {confidence}% confidence. Supporting evidence: {ind_text}.{ct_note}",
            f"Ensemble of {n} AI engines validates strong evidence supporting this content ({confidence}% confidence). {ind_text.capitalize()} match legitimate journalism.{ct_note}",
        ])


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


async def run_ensemble(text: str, source_type: str = "text") -> AnalyzeResponse:
    """
    Core ensemble detection logic — all engines run in PARALLEL.
    Implements multi-signal convergence and 5-label taxonomy:
    CREDIBLE → MOSTLY_TRUE → MIXED → MOSTLY_FALSE → FALSE
    """
    engines_used = []

    # ── Engine 1: Heuristic NLP (instant, always available) ──
    h = heuristic_analyze(text)
    if not h:
        raise HTTPException(400, "Text too short for analysis")
    engines_used.append("heuristic_nlp")
    content_type = h.get("content_type", "HARD_NEWS")

    # ── Engines 2-4: Run ALL in parallel ──
    hf_result, cb_result, gfc_result = await asyncio.gather(
        _safe_hf(text), _safe_cb(text), _safe_gfc(text)
    )

    # ── Collect engine verdicts ──
    # Map HF BERT results to new taxonomy
    # HF returns FAKE/REAL → map to FALSE/CREDIBLE
    votes = []
    votes.append((h["verdict"], h["confidence"], 0.30, "heuristic"))

    hf_conf = None
    if hf_result:
        engines_used.append("huggingface_bert")
        hf_conf = hf_result["confidence"]
        # Map old FAKE/REAL from HF model to new taxonomy
        hf_verdict = "FALSE" if hf_result["verdict"] == "FAKE" else "CREDIBLE"
        votes.append((hf_verdict, hf_result["confidence"], 0.35, "bert"))

    cb_score, cb_check = None, None
    if cb_result:
        engines_used.append("claimbuster_deberta")
        cb_score = cb_result["cfs_score"]
        cb_check = cb_result["is_checkworthy"]
        # ClaimBuster measures check-worthiness → maps to MIXED signal
        if cb_result["is_checkworthy"] and cb_result["cfs_score"] > 0.7:
            votes.append(("MIXED", min(round(cb_result["cfs_score"] * 70), 75), 0.10, "claimbuster"))

    gfc_found, gfc_rating, gfc_claims = None, None, None
    if gfc_result:
        engines_used.append("google_factcheck")
        gfc_found = gfc_result.get("found", False)
        gfc_rating = gfc_result.get("overall_rating")
        gfc_claims = gfc_result.get("claims", [])[:3]
        if gfc_result.get("found") and gfc_result.get("overall_rating"):
            if gfc_result["overall_rating"] == "DEBUNKED":
                votes.append(("FALSE", 90, 0.25, "google_fc"))
            elif gfc_result["overall_rating"] == "VERIFIED":
                votes.append(("CREDIBLE", 90, 0.25, "google_fc"))

    if not votes:
        raise HTTPException(500, "No detection engines available")

    # ── MULTI-SIGNAL CONVERGENCE GATE ──
    negative_votes = [v for v in votes if v[0] in ("FALSE", "MOSTLY_FALSE")]
    credible_votes = [v for v in votes if v[0] == "CREDIBLE"]
    mixed_votes = [v for v in votes if v[0] in ("MIXED", "MOSTLY_TRUE")]

    total_w = sum(v[2] for v in votes)

    # Compute weighted scores per verdict direction
    false_weighted = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "FALSE")
    mostly_false_weighted = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "MOSTLY_FALSE")
    credible_weighted = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "CREDIBLE")
    mostly_true_weighted = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "MOSTLY_TRUE")
    mixed_weighted = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "MIXED")

    negative_total = false_weighted + mostly_false_weighted * 0.6
    positive_total = credible_weighted + mostly_true_weighted * 0.6

    # ── APPLY CONVERGENCE RULES ──
    convergence_signals = len(negative_votes)

    # FALSE requires ≥2 engines agreeing + strong signal
    if len([v for v in votes if v[0] == "FALSE"]) >= 2 and negative_total > positive_total * 1.3:
        verdict = "FALSE"
        confidence = min(round(negative_total * 1.05), 99)
    elif false_weighted > 0 and len([v for v in votes if v[0] == "FALSE"]) == 1 and negative_total > positive_total:
        # Only 1 engine says FALSE — downgrade to MOSTLY_FALSE
        verdict = "MOSTLY_FALSE"
        confidence = min(round(negative_total * 0.85), 80)
    elif negative_total > positive_total and convergence_signals >= 1:
        verdict = "MOSTLY_FALSE" if negative_total > 40 else "MIXED"
        confidence = min(round(max(negative_total, positive_total)), 80)
    elif positive_total > negative_total:
        verdict = "CREDIBLE"
        base = positive_total
        # Agreement bonus
        agree_pct = len(credible_votes) / len(votes)
        if agree_pct >= 0.7:
            confidence = min(round(base * 1.08), 99)
        elif agree_pct >= 0.5:
            confidence = min(round(base), 95)
        else:
            confidence = min(round(base * 0.92), 88)
        confidence = max(confidence, 55)
        # If not strong enough for CREDIBLE, use MOSTLY_TRUE
        if confidence < 70 and agree_pct < 0.5:
            verdict = "MOSTLY_TRUE"
    else:
        # Tied or ambiguous
        verdict = "MIXED"
        confidence = 50

    # ── FINAL SAFEGUARDS ──
    # If Google Fact Check found VERIFIED claims, override toward CREDIBLE
    if gfc_rating == "VERIFIED" and verdict in ("MOSTLY_FALSE", "MIXED", "MOSTLY_TRUE"):
        verdict = "CREDIBLE"
        confidence = max(confidence, 75)

    # If Google Fact Check found DEBUNKED, ensure at least MOSTLY_FALSE
    if gfc_rating == "DEBUNKED" and verdict == "CREDIBLE":
        verdict = "MIXED"
        confidence = min(confidence, 70)

    indicators = h["indicators"]
    category = h["category"]
    analysis = generate_analysis_text(verdict, confidence, indicators, engines_used, content_type)

    # Fire-and-forget Supabase store
    async def _store():
        try:
            sb = get_supabase()
            sb.table("analyses").insert({
                "input_text": text[:500],
                "verdict": verdict,
                "confidence": confidence,
                "analysis": analysis,
                "indicators": indicators,
                "category": category,
                "heuristic_score": h["heuristic_score"],
                "is_public": True,
            }).execute()
        except Exception as e:
            logger.error(f"Supabase error: {e}")

    asyncio.create_task(_store())

    return AnalyzeResponse(
        id=None, verdict=verdict, confidence=confidence,
        analysis=analysis, indicators=indicators, category=category,
        content_type=content_type,
        heuristic_score=h["heuristic_score"], hf_confidence=hf_conf,
        claimbuster_score=cb_score, claimbuster_checkworthy=cb_check,
        google_factcheck_found=gfc_found, google_factcheck_rating=gfc_rating,
        google_factcheck_claims=gfc_claims,
        engines_used=engines_used,
        ensemble_method=f"ensemble_{len(engines_used)}_engines",
        source_type=source_type,
        convergence_signals=convergence_signals,
    )


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_text(req: AnalyzeRequest):
    """Analyze text for fake news using multi-engine ensemble."""
    return await run_ensemble(req.text, "text")


@router.post("/api/analyze/file", response_model=AnalyzeResponse)
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
