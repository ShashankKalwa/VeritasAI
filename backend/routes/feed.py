"""
GET /api/feed — Recent analyses feed endpoint (v2 taxonomy)
"""
import logging
from fastapi import APIRouter, Query, Request
from lib.feed_manager import get_feed as fetch_feed
from lib.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/feed")
@limiter.limit("60/minute")
async def live_feed(
    request: Request,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    source: str = Query(default="all"),
    verdict: str = Query(default=None),
):
    """Return recently analyzed articles from analyzed_news, newest first."""
    try:
        items = await fetch_feed(
            limit=limit,
            offset=offset,
            source=source,
            verdict=verdict,
        )
        return {"data": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Feed endpoint error: {e}")
        return {"data": [], "count": 0}
