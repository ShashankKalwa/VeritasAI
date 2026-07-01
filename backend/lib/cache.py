"""
Redis cache via Upstash REST API.
All operations are NON-FATAL — if Redis is unreachable, get_* returns
None (cache miss) and set_* silently no-ops. The pipeline must never
fail or slow down meaningfully because of a cache outage.
"""
import os, json, hashlib, logging
from upstash_redis import Redis

logger = logging.getLogger(__name__)

# Initialize _redis conditionally to avoid crash if env vars are missing
try:
    _redis = Redis(
        url=os.environ["UPSTASH_REDIS_URL"],
        token=os.environ["UPSTASH_REDIS_TOKEN"],
    )
except KeyError:
    _redis = None
    logger.warning("Upstash Redis credentials missing. Cache disabled.")

# TTLs (seconds) — overridable via env vars
TTL_TAVILY     = int(os.getenv("CACHE_TAVILY_TTL", "21600"))    # 6h
TTL_FACTCHECK  = int(os.getenv("CACHE_FACTCHECK_TTL", "43200")) # 12h
TTL_HF         = int(os.getenv("CACHE_HF_TTL", "86400"))        # 24h
TTL_EXTRACTION = int(os.getenv("CACHE_EXTRACTION_TTL", "86400"))# 24h

def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())

def _key(namespace: str, text: str) -> str:
    normalized = _normalize(text)
    h = hashlib.md5(normalized.encode()).hexdigest()
    return f"veritasai:{namespace}:{h}"

def _get(key: str):
    if _redis is None:
        return None
    try:
        raw = _redis.get(key)
        # upstash-redis might return a string or dict directly based on REST response
        if isinstance(raw, str):
            return json.loads(raw)
        return raw
    except Exception as e:
        logger.warning(f"Cache GET failed for {key}: {e}")
        return None

def _set(key: str, value, ttl: int):
    if _redis is None:
        return
    try:
        # upstash_redis handles dicts/lists serialization automatically in its current version, 
        # but json.dumps is safer if using strict REST. We'll use json.dumps for safety as specified.
        _redis.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.warning(f"Cache SET failed for {key}: {e}")

# ── Tavily ──────────────────────────────────────────────────────
def get_tavily(claim_text: str):
    return _get(_key("tavily", claim_text))

def set_tavily(claim_text: str, evidence: list):
    _set(_key("tavily", claim_text), evidence, TTL_TAVILY)

# ── Google Fact Check ───────────────────────────────────────────
def get_factcheck(claim_text: str):
    return _get(_key("factcheck", claim_text))

def set_factcheck(claim_text: str, results: list):
    _set(_key("factcheck", claim_text), results, TTL_FACTCHECK)

# ── HuggingFace (BERT + ClaimBuster) ────────────────────────────
def get_hf(model_id: str, input_text: str):
    return _get(_key(f"hf:{model_id}", input_text))

def set_hf(model_id: str, input_text: str, result):
    _set(_key(f"hf:{model_id}", input_text), result, TTL_HF)

# ── Gemini claim extraction ─────────────────────────────────────
def get_extraction(article_text: str):
    return _get(_key("extraction", article_text))

def set_extraction(article_text: str, claims: list):
    _set(_key("extraction", article_text), claims, TTL_EXTRACTION)

# ── Stats (for resume-worthy cache hit rate logging) ────────────
async def get_cache_stats() -> dict:
    """
    Returns rough cache health info. Used by GET /api/cache/stats
    (optional debug endpoint, useful for demo/interview purposes).
    """
    if _redis is None:
        return {"redis_connected": False, "error": "Missing credentials"}
    try:
        # Upstash doesn't expose hit/miss counters natively via REST,
        # so this is a lightweight connectivity check, not a full
        # metrics dashboard. Good enough for demo purposes.
        test_key = "veritasai:healthcheck"
        _redis.set(test_key, "ok", ex=10)
        result = _redis.get(test_key)
        return {"redis_connected": result == "ok"}
    except Exception as e:
        return {"redis_connected": False, "error": str(e)}
