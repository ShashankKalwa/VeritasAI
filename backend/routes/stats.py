"""
GET /api/stats — Dashboard statistics endpoint
"""
import logging
from fastapi import APIRouter
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/stats")
async def get_stats():
    """Return aggregated statistics for the dashboard."""
    try:
        sb = get_supabase()
        resp = sb.table("analyses").select("verdict, confidence, category, created_at").eq("is_public", True).execute()
        analyses = resp.data or []

        total = len(analyses)
        credible_count = sum(1 for a in analyses if a["verdict"] in ("CREDIBLE", "MOSTLY_TRUE"))
        false_count = sum(1 for a in analyses if a["verdict"] in ("FALSE", "MOSTLY_FALSE"))
        mixed_count = sum(1 for a in analyses if a["verdict"] == "MIXED")
        avg_confidence = round(sum(a["confidence"] for a in analyses) / total) if total > 0 else 0

        # By category
        cat_map = {}
        for a in analyses:
            cat = a["category"]
            if cat not in cat_map:
                cat_map[cat] = {"credible": 0, "false": 0}
            if a["verdict"] in ("FALSE", "MOSTLY_FALSE"):
                cat_map[cat]["false"] += 1
            else:
                cat_map[cat]["credible"] += 1

        by_category = sorted(
            [{"category": k, **v} for k, v in cat_map.items()],
            key=lambda x: x["credible"] + x["false"],
            reverse=True,
        )

        # Confidence distribution
        buckets = {"50-60": 0, "60-70": 0, "70-80": 0, "80-90": 0, "90-100": 0}
        for a in analyses:
            c = a["confidence"]
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

        return {
            "total": total,
            "credibleCount": credible_count,
            "falseCount": false_count,
            "mixedCount": mixed_count,
            "avgConfidence": avg_confidence,
            "byCategory": by_category,
            "confidenceBuckets": buckets,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"total": 0, "credibleCount": 0, "falseCount": 0, "mixedCount": 0, "avgConfidence": 0, "byCategory": [], "confidenceBuckets": {}}
