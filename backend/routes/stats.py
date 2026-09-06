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
            stats_data = resp.data
            
            # Fallback computation for graphs if RPC returns empty arrays/objects
            if not stats_data.get("byCategory") or not stats_data.get("confidenceBuckets"):
                raw_data = sb.table("analyses").select("category, overall_verdict, verdict, overall_confidence, confidence").order("created_at", desc=True).limit(1000).execute().data
                
                if not stats_data.get("byCategory"):
                    cat_map = {}
                    for row in raw_data:
                        cat = row.get("category", "General") or "General"
                        v = _get_verdict(row)
                        if cat not in cat_map:
                            cat_map[cat] = {"category": cat, "credible": 0, "false": 0, "mixed": 0}
                        
                        if v in CREDIBLE_VERDICTS:
                            cat_map[cat]["credible"] += 1
                        elif v in FALSE_VERDICTS:
                            cat_map[cat]["false"] += 1
                        elif v in MIXED_VERDICTS:
                            cat_map[cat]["mixed"] += 1
                    stats_data["byCategory"] = list(cat_map.values())
                
                if not stats_data.get("confidenceBuckets"):
                    buckets = {"0-20%": 0, "21-40%": 0, "41-60%": 0, "61-80%": 0, "81-100%": 0}
                    for row in raw_data:
                        conf = row.get("overall_confidence")
                        if conf is None:
                            conf = row.get("confidence", 0)
                        
                        if conf <= 20: buckets["0-20%"] += 1
                        elif conf <= 40: buckets["21-40%"] += 1
                        elif conf <= 60: buckets["41-60%"] += 1
                        elif conf <= 80: buckets["61-80%"] += 1
                        else: buckets["81-100%"] += 1
                    stats_data["confidenceBuckets"] = buckets
            
            return stats_data
            
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
