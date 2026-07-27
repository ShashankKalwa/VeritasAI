"""
GET /api/stats — Dashboard statistics endpoint (v2 taxonomy)
"""
import logging
from fastapi import APIRouter, Request
from lib.supabase_client import get_supabase
from lib.limiter import limiter

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
@limiter.limit("60/minute")
async def get_stats(request: Request):
    """Return aggregated statistics for the dashboard."""
    try:
        sb = get_supabase()
        resp = sb.rpc("get_dashboard_stats").execute()
        
        if resp.data:
            return resp.data
            
        return {
            "total": 0,
            "credibleCount": 0,
            "falseCount": 0,
            "mixedCount": 0,
            "opinionCount": 0,
            "insufficientCount": 0,
            "avgConfidence": 0,
            "byCategory": [],
            "confidenceBuckets": {},
            "verdictDistribution": {},
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "total": 0, "credibleCount": 0, "falseCount": 0,
            "mixedCount": 0, "opinionCount": 0, "insufficientCount": 0,
            "avgConfidence": 0, "byCategory": [], "confidenceBuckets": {},
            "verdictDistribution": {},
        }

@router.get("/api/cache/stats")
@limiter.limit("30/minute")
async def get_cache_status(request: Request):
    """Return health status of the Upstash Redis cache."""
    try:
        from lib.cache import get_cache_stats
        return await get_cache_stats()
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {"redis_connected": False, "error": str(e)}
