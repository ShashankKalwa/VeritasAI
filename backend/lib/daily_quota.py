"""
Per-IP daily quota for AI-heavy endpoints.

Try slowapi compound limits first:
    @limiter.limit("5/minute;200/day")

Only use this module if the compound limit syntax fails.
If compound limits work: DELETE THIS FILE.
"""
import os
import logging
from datetime import datetime
from fastapi import Request, HTTPException
from lib.cache import _redis

logger = logging.getLogger(__name__)

DAILY_LIMIT_ANALYZE = int(os.getenv("DAILY_LIMIT_ANALYZE", "200"))

async def check_daily_quota(
    request: Request,
    limit: int = DAILY_LIMIT_ANALYZE
):
    """
    FastAPI Dependency — attach to endpoints requiring a daily quota.

    Usage:
        @router.post("/api/analyze")
        async def analyze(request: Request,
                          _quota=Depends(check_daily_quota)):
    """
    from lib.limiter import _get_client_ip
    client_ip = _get_client_ip(request)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key = f"veritasai:daily:{today}:{client_ip}"

    try:
        count = _redis.incr(redis_key)
        if count == 1:
            # First request today — set TTL to 25 hours (buffer for timezone skew)
            _redis.expire(redis_key, 90000)
        if count > limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Daily limit of {limit} requests exceeded. "
                    "Resets at midnight UTC."
                ),
                headers={"Retry-After": "86400"}
            )
    except HTTPException:
        raise   # re-raise 429 — this is intentional, not an error
    except Exception as e:
        # Redis failure — fail open (allow the request through)
        logger.warning(f"Daily quota check failed: {e}. Allowing request.")
