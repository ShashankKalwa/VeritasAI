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


def generate_analysis_text(verdict, confidence, indicators, engines):
    ind_text = ", ".join(indicators[:3]).lower() if indicators else "general pattern analysis"
    n = len(engines)
    if verdict == "FAKE":
        return random.choice([
            f"Multi-engine analysis ({n} engines) reveals significant misinformation patterns with {confidence}% confidence. Key red flags: {ind_text}.",
            f"Ensemble of {n} AI engines flags this as likely misinformation ({confidence}% confidence). Detected {ind_text}.",
            f"Cross-referenced across {n} engines — multiple fake news indicators found. {ind_text.capitalize()} strongly suggest misleading content ({confidence}%).",
        ])
    else:
        return random.choice([
            f"Multi-engine verification ({n} engines) confirms legitimate reporting with {confidence}% confidence. Positive signals: {ind_text}.",
            f"Ensemble of {n} AI engines validates this content ({confidence}% confidence). {ind_text.capitalize()} match credible journalism.",
            f"Cross-referenced across {n} engines — credibility markers detected. {ind_text.capitalize()} support authenticity ({confidence}%).",
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
    """Core ensemble detection logic — all engines run in PARALLEL."""
    engines_used = []
    votes = []

    # Engine 1: Heuristic NLP (instant, always available)
    h = heuristic_analyze(text)
    if not h:
        raise HTTPException(400, "Text too short for analysis")
    engines_used.append("heuristic_nlp")
    votes.append(("FAKE" if h["verdict"] == "FAKE" else "REAL", h["confidence"], 0.30))

    # Engines 2-4: Run ALL in parallel (max 4s timeout)
    hf_result, cb_result, gfc_result = await asyncio.gather(
        _safe_hf(text), _safe_cb(text), _safe_gfc(text)
    )

    # Process HF BERT result
    hf_conf = None
    if hf_result:
        engines_used.append("huggingface_bert")
        hf_conf = hf_result["confidence"]
        votes.append((hf_result["verdict"], hf_result["confidence"], 0.35))

    # Process ClaimBuster result
    cb_score, cb_check = None, None
    if cb_result:
        engines_used.append("claimbuster_deberta")
        cb_score = cb_result["cfs_score"]
        cb_check = cb_result["is_checkworthy"]
        if cb_result["is_checkworthy"]:
            votes.append(("FAKE", min(round(cb_result["cfs_score"] * 80), 80), 0.15))

    # Process Google Fact Check result
    gfc_found, gfc_rating, gfc_claims = None, None, None
    if gfc_result:
        engines_used.append("google_factcheck")
        gfc_found = gfc_result.get("found", False)
        gfc_rating = gfc_result.get("overall_rating")
        gfc_claims = gfc_result.get("claims", [])[:3]
        if gfc_result.get("found") and gfc_result.get("overall_rating"):
            if gfc_result["overall_rating"] == "DEBUNKED":
                votes.append(("FAKE", 90, 0.20))
            elif gfc_result["overall_rating"] == "VERIFIED":
                votes.append(("REAL", 90, 0.20))

    # Ensemble merge
    if not votes:
        raise HTTPException(500, "No detection engines available")

    total_w = sum(v[2] for v in votes)
    fake_w = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "FAKE")
    real_w = sum(v[1] * (v[2] / total_w) for v in votes if v[0] == "REAL")

    verdict = "FAKE" if fake_w > real_w else "REAL"
    base = max(fake_w, real_w)

    fake_c = sum(1 for v in votes if v[0] == "FAKE")
    agree = max(fake_c, len(votes) - fake_c) / len(votes)
    if agree >= 0.8:
        confidence = min(round(base * 1.05), 99)
    elif agree >= 0.6:
        confidence = min(round(base), 95)
    else:
        confidence = min(round(base * 0.9), 85)
    confidence = max(confidence, 51)

    indicators = h["indicators"]
    category = h["category"]
    analysis = generate_analysis_text(verdict, confidence, indicators, engines_used)

    # Fire-and-forget Supabase store (don't block response)
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
        heuristic_score=h["heuristic_score"], hf_confidence=hf_conf,
        claimbuster_score=cb_score, claimbuster_checkworthy=cb_check,
        google_factcheck_found=gfc_found, google_factcheck_rating=gfc_rating,
        google_factcheck_claims=gfc_claims,
        engines_used=engines_used,
        ensemble_method=f"ensemble_{len(engines_used)}_engines",
        source_type=source_type,
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
