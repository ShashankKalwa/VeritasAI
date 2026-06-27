"""
VeritasAI — Trending & Feed API Routes (Phase 8)
GET /api/trending  — trending claims sorted by check_count
GET /api/feed      — live feed from analyzed_news (replaces old feed)
POST /api/vote     — thumbs up/down on a verdict
POST /api/trending/refresh — manually trigger trending cron
"""
import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from lib.supabase_client import get_supabase
from lib.feed_manager import get_feed, get_trending

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/trending")
async def trending_claims(
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


@router.get("/api/feed")
async def live_feed(
    limit: int = Query(default=20, le=50),
    offset: int = Query(default=0, ge=0),
    source: str = Query(default="all"),
    verdict: str = Query(default=None),
):
    """Return recently analyzed articles from analyzed_news, newest first."""
    try:
        items = await get_feed(
            limit=limit,
            offset=offset,
            source=source,
            verdict=verdict,
        )
        return {"data": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Feed endpoint error: {e}")
        return {"data": [], "count": 0}


class VoteRequest(BaseModel):
    news_id: str
    vote: str  # 'true' or 'false'


@router.post("/api/vote")
async def submit_vote(req: VoteRequest):
    """Simple thumbs-up / thumbs-down on a verdict."""
    if req.vote not in ("true", "false"):
        raise HTTPException(400, "Vote must be 'true' or 'false'")

    try:
        sb = get_supabase()

        # Get current counts
        current = (
            sb.table("analyzed_news")
            .select("vote_true, vote_false")
            .eq("id", req.news_id)
            .limit(1)
            .execute()
        )

        if not current.data:
            raise HTTPException(404, "Article not found")

        row = current.data[0]

        if req.vote == "true":
            new_true = row["vote_true"] + 1
            new_false = row["vote_false"]
        else:
            new_true = row["vote_true"]
            new_false = row["vote_false"] + 1

        sb.table("analyzed_news").update({
            "vote_true": new_true,
            "vote_false": new_false,
        }).eq("id", req.news_id).execute()

        return {
            "news_id": req.news_id,
            "vote_true": new_true,
            "vote_false": new_false,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vote error: {e}")
        raise HTTPException(500, f"Vote failed: {str(e)[:100]}")


@router.post("/api/trending/refresh")
async def refresh_trending():
    """Manually trigger the trending cron job."""
    try:
        from jobs.trending_cron import run_trending_analysis
        import asyncio
        asyncio.create_task(run_trending_analysis())
        return {"status": "triggered", "message": "Trending analysis started in background"}
    except Exception as e:
        logger.error(f"Manual refresh error: {e}")
        raise HTTPException(500, f"Refresh failed: {str(e)[:100]}")
