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

def schedule_keep_alive(scheduler):
    """Add keep-alive job to the given APScheduler."""
    scheduler.add_job(
        ping_server,
        trigger='interval',
        minutes=14,
        id='keep_alive_ping',
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),
    )
    logger.info("📅 Keep-alive cron scheduled: every 14 minutes")
