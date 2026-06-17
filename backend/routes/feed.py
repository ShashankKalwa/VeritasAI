"""
GET /api/feed — Recent analyses feed endpoint (v2 taxonomy)
"""
import logging
from fastapi import APIRouter, Query
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/feed")
async def get_feed(limit: int = Query(default=10, le=50)):
    """Return recent public analyses for the community feed."""
    try:
        sb = get_supabase()
        resp = (
            sb.table("analyses")
            .select("id, input_text, verdict, confidence, category, created_at, "
                    "overall_verdict, overall_confidence, claim_count, top_sources, content_type")
            .eq("is_public", True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        items = resp.data or []

        # Enrich feed items with v2 fields (backward compatible)
        for item in items:
            # Use overall_verdict if available, fall back to old verdict
            if not item.get("overall_verdict"):
                old_verdict = item.get("verdict", "")
                item["overall_verdict"] = _map_old_verdict(old_verdict)
            if item.get("overall_confidence") is None:
                item["overall_confidence"] = item.get("confidence")
            if not item.get("claim_count"):
                item["claim_count"] = 0
            if not item.get("top_sources"):
                item["top_sources"] = []

        return {"data": items}
    except Exception as e:
        logger.error(f"Feed error: {e}")
        return {"data": []}


def _map_old_verdict(verdict: str) -> str:
    """Map old verdict labels to new v2 taxonomy."""
    mapping = {
        "CREDIBLE": "Credible",
        "MOSTLY_TRUE": "Likely True",
        "MIXED": "Mixed / Misleading",
        "MOSTLY_FALSE": "Likely False",
        "FALSE": "False",
        "REAL": "Credible",
        "FAKE": "False",
    }
    return mapping.get(verdict, verdict)
