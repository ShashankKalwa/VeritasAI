import os
import logging
import httpx
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

async def ping_server():
    """Ping the server itself to prevent Render from sleeping."""
    # Render automatically sets RENDER_EXTERNAL_URL for web services
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        # Fallback for local testing or custom environments
        url = os.getenv("SERVER_URL")
        
    if not url:
        logger.debug("RENDER_EXTERNAL_URL not set, skipping keep-alive ping")
        return

    try:
        # Ping the health endpoint
        health_url = f"{url}/health"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(health_url)
            logger.info(f"Keep-alive ping to {health_url} - Status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Keep-alive ping failed: {e}")

async def ping_supabase():
    """Ping Supabase to prevent the free-tier database from being paused."""
    try:
        from lib.supabase_client import get_supabase
        sb = get_supabase()
        # A lightweight query to keep the database active
        sb.table("analyzed_news").select("id").limit(1).execute()
        logger.info("Keep-alive ping to Supabase - Status: Success")
    except Exception as e:
        logger.error(f"Supabase keep-alive ping failed: {e}")

async def ping_redis():
    """Ping Upstash Redis to prevent the free-tier database from being paused."""
    try:
        from lib.cache import get_cache_stats
        result = await get_cache_stats()
        if result.get("redis_connected"):
            logger.info("Keep-alive ping to Upstash Redis - Status: Success")
        else:
            logger.warning(f"Keep-alive ping to Upstash Redis - Status: Failed {result.get('error')}")
    except Exception as e:
        logger.error(f"Redis keep-alive ping failed: {e}")

def schedule_keep_alive(scheduler):
    """Add keep-alive jobs to the given APScheduler."""
    scheduler.add_job(
        ping_server,
        trigger='interval',
        minutes=14,
        id='keep_alive_ping',
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    logger.info("📅 Render Keep-alive cron scheduled: every 14 minutes")
    
    scheduler.add_job(
        ping_supabase,
        trigger='interval',
        hours=12,  # Running every 12 hours is enough to keep Supabase awake
        id='supabase_keep_alive_ping',
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    logger.info("📅 Supabase Keep-alive cron scheduled: every 12 hours")
    
    scheduler.add_job(
        ping_redis,
        trigger='interval',
        hours=12,  # Running every 12 hours is enough to keep Upstash Redis awake
        id='redis_keep_alive_ping',
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    logger.info("📅 Upstash Redis Keep-alive cron scheduled: every 12 hours")
