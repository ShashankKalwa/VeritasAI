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
        fake_count = sum(1 for a in analyses if a["verdict"] == "FAKE")
        real_count = sum(1 for a in analyses if a["verdict"] == "REAL")
        avg_confidence = round(sum(a["confidence"] for a in analyses) / total) if total > 0 else 0

        # By category
        cat_map = {}
        for a in analyses:
            cat = a["category"]
            if cat not in cat_map:
                cat_map[cat] = {"fake": 0, "real": 0}
            if a["verdict"] == "FAKE":
                cat_map[cat]["fake"] += 1
            else:
                cat_map[cat]["real"] += 1

        by_category = sorted(
            [{"category": k, **v} for k, v in cat_map.items()],
            key=lambda x: x["fake"] + x["real"],
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
            "fakeCount": fake_count,
            "realCount": real_count,
            "avgConfidence": avg_confidence,
            "byCategory": by_category,
            "confidenceBuckets": buckets,
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {"total": 0, "fakeCount": 0, "realCount": 0, "avgConfidence": 0, "byCategory": [], "confidenceBuckets": {}}
