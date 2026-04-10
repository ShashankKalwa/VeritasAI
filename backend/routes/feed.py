"""
GET /api/feed — Recent analyses feed endpoint
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
            .select("*")
            .eq("is_public", True)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"data": resp.data or []}
    except Exception as e:
        logger.error(f"Feed error: {e}")
        return {"data": []}
