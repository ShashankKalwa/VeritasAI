"""
GET /api/stats — Dashboard statistics endpoint (v2 taxonomy)
"""
import logging
from fastapi import APIRouter
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()

# v2 verdict taxonomy
CREDIBLE_VERDICTS = {"Credible", "Likely True", "CREDIBLE", "MOSTLY_TRUE"}
FALSE_VERDICTS = {"False", "Likely False", "FALSE", "MOSTLY_FALSE"}
MIXED_VERDICTS = {"Mixed / Misleading", "MIXED"}
OPINION_VERDICTS = {"Opinion / Not Fact-Checkable"}
INSUFFICIENT_VERDICTS = {"Insufficient Evidence"}


def _get_verdict(row):
    """Get verdict from row, preferring overall_verdict over old verdict field."""
    return row.get("overall_verdict") or row.get("verdict", "Insufficient Evidence")


@router.get("/api/stats")
async def get_stats():
    """Return aggregated statistics for the dashboard."""
    try:
        sb = get_supabase()
        resp = sb.table("analyses").select(
            "verdict, overall_verdict, confidence, overall_confidence, category, created_at"
        ).eq("is_public", True).execute()
        analyses = resp.data or []

        total = len(analyses)
        credible_count = sum(1 for a in analyses if _get_verdict(a) in CREDIBLE_VERDICTS)
        false_count = sum(1 for a in analyses if _get_verdict(a) in FALSE_VERDICTS)
        mixed_count = sum(1 for a in analyses if _get_verdict(a) in MIXED_VERDICTS)
        opinion_count = sum(1 for a in analyses if _get_verdict(a) in OPINION_VERDICTS)
        insufficient_count = sum(1 for a in analyses if _get_verdict(a) in INSUFFICIENT_VERDICTS)

        avg_confidence = 0
        confidences = [a.get("overall_confidence") or a.get("confidence") or 0 for a in analyses]
        if confidences:
            avg_confidence = round(sum(confidences) / len(confidences))

        # By category
        cat_map = {}
        for a in analyses:
            cat = a.get("category", "General")
            if cat not in cat_map:
                cat_map[cat] = {"credible": 0, "false": 0, "mixed": 0}
            v = _get_verdict(a)
            if v in FALSE_VERDICTS:
                cat_map[cat]["false"] += 1
            elif v in MIXED_VERDICTS:
                cat_map[cat]["mixed"] += 1
            else:
                cat_map[cat]["credible"] += 1

        by_category = sorted(
            [{"category": k, **v} for k, v in cat_map.items()],
            key=lambda x: x["credible"] + x["false"] + x["mixed"],
            reverse=True,
        )

        # Confidence distribution
        buckets = {"50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
        for c in confidences:
            if c < 60:
                buckets["50-60"] += 1
            elif c < 70:
                buckets["60-70"] += 1
            elif c < 80:
                buckets["70-80"] += 1
            elif c < 90:
                buckets["80-90"] += 1
            else:
                buckets["90-100"] += 1

        # Verdict distribution (new v2 taxonomy)
        verdict_distribution = {
            "Credible": credible_count,
            "False": false_count,
            "Mixed / Misleading": mixed_count,
            "Opinion / Not Fact-Checkable": opinion_count,
            "Insufficient Evidence": insufficient_count,
        }

        return {
            "total": total,
            "credibleCount": credible_count,
            "falseCount": false_count,
            "mixedCount": mixed_count,
            "opinionCount": opinion_count,
            "insufficientCount": insufficient_count,
            "avgConfidence": avg_confidence,
            "byCategory": by_category,
            "confidenceBuckets": buckets,
            "verdictDistribution": verdict_distribution,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total": 0, "credibleCount": 0, "falseCount": 0,
            "mixedCount": 0, "opinionCount": 0, "insufficientCount": 0,
            "avgConfidence": 0, "byCategory": [], "confidenceBuckets": {},
            "verdictDistribution": {},
        }
