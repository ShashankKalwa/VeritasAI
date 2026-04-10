"""
POST /api/analyze — Core detection endpoint
Runs ensemble of ML model + heuristic engine.
"""
import re
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from lib.heuristics import heuristic_analyze
from lib.ml_model import get_classifier
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


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
    ml_confidence: int | None = None
    ensemble_method: str = "heuristic+ml"


def generate_analysis_text(verdict: str, confidence: int, indicators: list[str]) -> str:
    """Generate human-readable analysis text."""
    ind_text = ", ".join(indicators[:3]).lower() if indicators else "general pattern analysis"

    if verdict == "FAKE":
        templates = [
            f"This text exhibits classic misinformation patterns with {confidence}% confidence. Key red flags include {ind_text}. The language patterns are inconsistent with legitimate journalism.",
            f"Analysis reveals significant misinformation markers ({confidence}% confidence). Detected {ind_text}, suggesting this follows established fake news patterns.",
            f"Multiple fake news indicators detected. The presence of {ind_text} strongly suggests this content is designed to mislead ({confidence}% confidence).",
        ]
    else:
        templates = [
            f"This text demonstrates legitimate reporting characteristics with {confidence}% confidence. Positive signals include {ind_text}.",
            f"Analysis indicates genuine news content ({confidence}% confidence). {ind_text.capitalize()} are consistent with credible journalism standards.",
            f"The text exhibits credibility markers typical of authentic sources. {ind_text.capitalize()} support the assessment ({confidence}% confidence).",
        ]

    import random
    return random.choice(templates)


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_article(req: AnalyzeRequest):
    """Analyze text for fake news using ensemble of ML + heuristics."""
    text = req.text

    # 1. Run heuristic analysis
    heuristic_result = heuristic_analyze(text)
    if not heuristic_result:
        raise HTTPException(status_code=400, detail="Analysis failed")

    # 2. Run ML model
    ml_classifier = get_classifier()
    ml_result = ml_classifier.predict(text)

    # 3. Ensemble: combine ML (60%) + heuristic (40%)
    if ml_result:
        ml_fake = ml_result["verdict"] == "FAKE"
        h_fake = heuristic_result["verdict"] == "FAKE"

        ml_conf = ml_result["confidence"]
        h_conf = heuristic_result["confidence"]

        if ml_fake == h_fake:
            # Agree — use weighted average confidence
            verdict = "FAKE" if ml_fake else "REAL"
            confidence = min(round(ml_conf * 0.6 + h_conf * 0.4), 99)
        else:
            # Disagree — trust ML more but cap confidence
            if ml_conf > h_conf + 15:
                verdict = ml_result["verdict"]
                confidence = min(round(ml_conf * 0.55 + h_conf * 0.2), 85)
            else:
                verdict = heuristic_result["verdict"]
                confidence = min(round(h_conf * 0.55 + ml_conf * 0.2), 80)

        ml_confidence = ml_result["confidence"]
    else:
        # ML not available — use heuristic only
        verdict = heuristic_result["verdict"]
        confidence = heuristic_result["confidence"]
        ml_confidence = None

    indicators = heuristic_result["indicators"]
    category = heuristic_result["category"]
    analysis = generate_analysis_text(verdict, confidence, indicators)

    # 4. Store in Supabase
    stored_id = None
    try:
        sb = get_supabase()
        resp = sb.table("analyses").insert({
            "input_text": text,
            "verdict": verdict,
            "confidence": confidence,
            "analysis": analysis,
            "indicators": indicators,
            "category": category,
            "heuristic_score": heuristic_result["heuristic_score"],
            "llm_verdict": ml_result["verdict"] if ml_result else None,
            "is_public": True,
        }).execute()

        if resp.data:
            stored_id = resp.data[0]["id"]
    except Exception as e:
        logger.error(f"Supabase insert error: {e}")

    return AnalyzeResponse(
        id=stored_id,
        verdict=verdict,
        confidence=confidence,
        analysis=analysis,
        indicators=indicators,
        category=category,
        heuristic_score=heuristic_result["heuristic_score"],
        ml_confidence=ml_confidence,
        ensemble_method="heuristic+ml" if ml_result else "heuristic_only",
    )
