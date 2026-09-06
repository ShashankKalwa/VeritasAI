"""
VeritasAI v2 — Ensemble Verdict v2
Step 11: Credibility-weighted per-claim + overall article verdict.

IMPORTANT:
    - ClaimBuster score has weight = 0 in the ensemble (informational only)
    - Evidence weighting is credibility-score-based, NOT simple source count
    - 5 low-score blogs (score 20 each) ≈ 1 Reuters article (score 95)
"""
import logging

logger = logging.getLogger(__name__)

# Verdict taxonomy — labels + score thresholds + colors
VERDICT_TAXONOMY = [
    {"label": "Credible",                     "min": 0.60, "max": 1.00,  "color": "#22c55e"},
    {"label": "Likely True",                  "min": 0.20, "max": 0.60,  "color": "#86efac"},
    {"label": "Mixed / Misleading",           "min": -0.20, "max": 0.20, "color": "#eab308"},
    {"label": "Likely False",                 "min": -0.60, "max": -0.20, "color": "#f97316"},
    {"label": "False",                        "min": -1.00, "max": -0.60, "color": "#ef4444"},
]

VERDICT_COLORS = {
    "Credible": "#22c55e",
    "Likely True": "#86efac",
    "Mixed / Misleading": "#eab308",
    "Likely False": "#f97316",
    "False": "#ef4444",
    "Insufficient Evidence": "#94a3b8",
    "Opinion / Not Fact-Checkable": "#6366f1",
}

# Ensemble weights — ClaimBuster is explicitly 0
WEIGHTS = {
    "evidence": 0.65,           # Boosted: Evidence should dominate the verdict
    "google_factcheck": 0.15,   # High signal if verified fact-check match found
    "bert_linguistic": 0.10,    # Reduced: BERT writing style shouldn't overpower facts
    "heuristic_manipulation": 0.10,  # Reduced: Heuristics shouldn't overpower facts
    "claimbuster": 0.00,        # Informational only — NEVER part of score
}


def compute_claim_verdict(
    reasoning: dict,
    bert_signal: float,
    manipulation_signal: float,
    google_factcheck_match: bool = False,
) -> dict:
    """
    Compute verdict for a single check-worthy claim.

    Per-claim scoring:
        evidence_score = (
          sum(credibility_score for supporting) -
          sum(credibility_score for contradicting)
        ) / max(total_credibility_sum, 1)
        Range: -1.0 (all contradiction) to +1.0 (all support)

    Weighted final score:
        final_score = (
          evidence_score        * 0.50
          + google_factcheck    * 0.15
          + linguistic_signal   * 0.15
          + manipulation_signal * 0.20
        )
        Range: -1.0 to +1.0

    Args:
        reasoning: dict from evidence_reasoner with supporting/contradicting/unclear.
        bert_signal: BERT linguistic credibility signal (0-100).
        manipulation_signal: Heuristic manipulation signal (0-100).
        google_factcheck_match: Whether Google Fact Check found a match.

    Returns:
        dict with: verdict, confidence, final_score, evidence_score.
    """
    supporting = reasoning.get("supporting_evidence", [])
    contradicting = reasoning.get("contradicting_evidence", [])
    unclear = reasoning.get("unclear_evidence", [])

    # Check if we have any evidence at all
    all_evidence = supporting + contradicting + unclear
    if not all_evidence:
        return {
            "verdict": "Insufficient Evidence",
            "confidence": None,
            "final_score": 0.0,
            "evidence_score": 0.0,
        }

    # Evidence score: credibility-weighted, not source count
    support_weight = sum(e.get("credibility_score", 40) for e in supporting)
    contradict_weight = sum(e.get("credibility_score", 40) for e in contradicting)
    total_weight = support_weight + contradict_weight + sum(
        e.get("credibility_score", 40) for e in unclear
    )

    if total_weight > 0:
        evidence_score = (support_weight - contradict_weight) / total_weight
    else:
        evidence_score = 0.0

    # Normalize signals to -1.0 to +1.0 range
    # bert_signal: 0-100, where 100 = credible → map to -1 to +1
    bert_normalized = (bert_signal - 50) / 50  # 50 → 0, 100 → +1, 0 → -1

    # manipulation_signal: 0-100, where 100 = no manipulation → map to -1 to +1
    manip_normalized = (manipulation_signal - 50) / 50

    # Google Fact Check: binary → +0.8 if verified match, 0 if no match
    # Check the fact-check details for DEBUNKED vs VERIFIED
    gfc_score = 0.0
    if google_factcheck_match:
        gfc_details = reasoning.get("google_factcheck_details", "")
        if gfc_details:
            details_lower = gfc_details.lower()
            if any(w in details_lower for w in ["false", "debunked", "misleading", "incorrect", "pants on fire", "satire", "fake", "hoax"]):
                gfc_score = -0.8
            elif any(w in details_lower for w in ["true", "correct", "verified", "accurate"]):
                gfc_score = 0.8
            else:
                gfc_score = 0.0  # Mixed or unclear

    # Weighted final score
    final_score = (
        evidence_score * WEIGHTS["evidence"]
        + gfc_score * WEIGHTS["google_factcheck"]
        + bert_normalized * WEIGHTS["bert_linguistic"]
        + manip_normalized * WEIGHTS["heuristic_manipulation"]
        # ClaimBuster weight is 0 — explicitly excluded
    )

    # Clamp to [-1, 1]
    final_score = max(min(final_score, 1.0), -1.0)

    # Map to verdict label
    verdict = _score_to_verdict(final_score)

    # Confidence = abs(final_score) * 100, clamped 0-100
    confidence = min(round(abs(final_score) * 100), 100)

    return {
        "verdict": verdict,
        "confidence": confidence,
        "final_score": round(final_score, 4),
        "evidence_score": round(evidence_score, 4),
    }


def compute_overall_verdict(claims: list[dict]) -> dict:
    """
    Derive overall article verdict from per-claim verdicts.

    Worst-case dominant rule:
        - If any claim = "False" with confidence > 70 → article = "False"
        - Else: weighted average of per-claim final_scores
          (weight = claim position, claim 1 = highest weight)

    Returns:
        dict with: overall_verdict, overall_confidence.
    """
    if not claims:
        return {
            "overall_verdict": "Insufficient Evidence",
            "overall_confidence": None,
        }

    # Filter to check-worthy claims only
    checkworthy = [c for c in claims if c.get("check_worthy", True)]
    if not checkworthy:
        return {
            "overall_verdict": "Opinion / Not Fact-Checkable",
            "overall_confidence": None,
        }

    # Rule 1: If any claim is "False" with confidence > 70, article is "False"
    for c in checkworthy:
        if c.get("verdict") == "False" and (c.get("confidence") or 0) > 70:
            return {
                "overall_verdict": "False",
                "overall_confidence": c.get("confidence"),
            }

    # Rule 2: Weighted average of per-claim final_scores
    # Weight = position-based (claim 1 gets highest weight)
    total_weighted_score = 0.0
    total_weight = 0.0
    for i, c in enumerate(checkworthy):
        weight = len(checkworthy) - i  # First claim gets highest weight
        score = c.get("final_score", 0.0)
        total_weighted_score += score * weight
        total_weight += weight

    if total_weight > 0:
        avg_score = total_weighted_score / total_weight
    else:
        avg_score = 0.0

    overall_verdict = _score_to_verdict(avg_score)
    overall_confidence = min(round(abs(avg_score) * 100), 100)

    return {
        "overall_verdict": overall_verdict,
        "overall_confidence": overall_confidence,
    }


def _score_to_verdict(score: float) -> str:
    """Map a -1.0 to +1.0 score to a verdict label."""
    if score >= 0.60:
        return "Credible"
    elif score >= 0.20:
        return "Likely True"
    elif score >= -0.20:
        return "Mixed / Misleading"
    elif score >= -0.60:
        return "Likely False"
    else:
        return "False"
