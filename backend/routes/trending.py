"""
VeritasAI — Trending & Feed API Routes (Phase 8)
GET /api/trending  — trending claims sorted by check_count
GET /api/feed      — live feed from analyzed_news (replaces old feed)
POST /api/vote     — thumbs up/down on a verdict
POST /api/trending/refresh — manually trigger trending cron
"""
import logging
import os
from fastapi import APIRouter, HTTPException, Query, Request, Header, Depends
from pydantic import BaseModel
from lib.supabase_client import get_supabase
from lib.feed_manager import get_trending
from lib.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

def require_admin_key(x_admin_key: str = Header(default=None)):
    admin_key = os.getenv("ADMIN_API_KEY")
    if not admin_key:
        return
    if x_admin_key != admin_key:
        raise HTTPException(
            status_code=403,
            detail="Access denied. X-Admin-Key header required."
        )

@router.get("/api/trending")
@limiter.limit("60/minute")
async def trending_claims(
    request: Request,
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    verdict: str = Query(default=None),
):
    """Return trending claims sorted by check_count DESC."""
    try:
        items = await get_trending(limit=limit, offset=offset, verdict=verdict)
        return {"data": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Trending endpoint error: {e}")
        return {"data": [], "count": 0}







@router.post("/api/trending/refresh")
@limiter.limit("2/minute")
async def refresh_trending(
    request: Request,
    _admin=Depends(require_admin_key)
):
    """Manually trigger the trending cron job."""
    try:
        from jobs.trending_cron import run_trending_analysis
        import asyncio
        asyncio.create_task(run_trending_analysis())
        return {"status": "triggered", "message": "Trending analysis started in background"}
    except Exception as e:
        logger.error(f"Manual refresh error: {e}")
        raise HTTPException(500, f"Refresh failed: {str(e)[:100]}")
