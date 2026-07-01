"""
Centralized SlowAPI rate limiter.
- IP-based key function only (no auth, no JWT).
- Redis backend (Upstash protocol connection) for persistence
  across restarts and Render deployments.
- Fail-open on Redis errors — if Redis is down, requests pass through.
"""
import os
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

logger = logging.getLogger(__name__)

# ── Redis storage backend ──────────────────────────────────────────
# Upstash provides two connection modes:
#   - REST API       → used by cache.py (upstash-redis package)
#   - Redis Protocol → required by the limits library used by slowapi
#
# Get your protocol URL from Upstash dashboard:
#   Database → Details → "Redis CLI" section
#   Format: redis://default:<password>@<host>:<port>
# Add it to backend/.env as UPSTASH_REDIS_PROTOCOL_URL

def _build_storage():
    protocol_url = os.getenv("UPSTASH_REDIS_PROTOCOL_URL")
    if not protocol_url:
        logger.warning(
            "UPSTASH_REDIS_PROTOCOL_URL not set. "
            "Rate limiter will use in-process memory storage. "
            "Limits will NOT persist across restarts."
        )
        return "memory://"
    try:
        from limits.storage import RedisStorage
        # Just initialize it to test connection, if it fails it goes to except
        storage = RedisStorage(protocol_url)
        logger.info("Rate limiter: connected to Upstash Redis storage.")
        return protocol_url
    except Exception as e:
        logger.error(
            f"Rate limiter: Redis connection failed ({e}). "
            "Falling back to in-process memory storage."
        )
        return "memory://"

# ── IP-based key function ──────────────────────────────────────────
def _get_client_ip(request: Request) -> str:
    """
    Extract the real client IP address.
    Respects X-Forwarded-For set by Render's reverse proxy and Cloudflare.
    Always returns the original client IP, not the proxy IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be a comma-separated chain: "client, proxy1, proxy2"
        # Take the first entry — the original client IP
        return forwarded_for.split(",")[0].strip()
    # Fallback: direct connection (local dev without proxy)
    return get_remote_address(request)

# ── Limiter instance ───────────────────────────────────────────────
_storage = _build_storage()

limiter = Limiter(
    key_func=_get_client_ip,
    storage_uri=_storage,
    default_limits=[],  # no global default — set per-endpoint explicitly
)
