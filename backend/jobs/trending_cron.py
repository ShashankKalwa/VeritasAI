"""
VeritasAI — Trending Cron Job
Fetches top headlines from NewsAPI every N hours and auto-analyzes them.
Uses APScheduler (AsyncIOScheduler) — runs inside the FastAPI process.
"""
import os
import hashlib
import re
import logging
from datetime import datetime, timezone, timedelta

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_LANGUAGE = os.getenv("NEWS_API_LANGUAGE", "en")
NEWS_API_PAGE_SIZE = int(os.getenv("NEWS_API_PAGE_SIZE", "10"))
FEED_SKIP_HOURS = int(os.getenv("FEED_SKIP_IF_ANALYZED_WITHIN_HOURS", "12"))
CRON_INTERVAL = int(os.getenv("FEED_CRON_INTERVAL_HOURS", "3"))


def _normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _md5(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


async def fetch_headlines() -> list[dict]:
    """Fetch top headlines from NewsAPI."""
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set — skipping headline fetch")
        return []

    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": NEWS_API_LANGUAGE,
        "pageSize": NEWS_API_PAGE_SIZE,
        "apiKey": NEWS_API_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            articles = data.get("articles", [])
            logger.info(f"NewsAPI: fetched {len(articles)} headlines")
            return articles
    except Exception as e:
        logger.error(f"NewsAPI fetch error: {e}")
        return []


async def should_skip(headline_hash: str) -> bool:
    """Check if this headline was analyzed recently (within FEED_SKIP_HOURS)."""
    try:
        from lib.supabase_client import get_supabase
        sb = get_supabase()

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=FEED_SKIP_HOURS)).isoformat()

        resp = (
            sb.table("analyzed_news")
            .select("id, last_analyzed_at")
            .eq("headline_hash", headline_hash)
            .gte("last_analyzed_at", cutoff)
            .limit(1)
            .execute()
        )

        return bool(resp.data)
    except Exception as e:
        logger.error(f"Skip check error: {e}")
        return False


async def run_trending_analysis():
    """
    Main cron job function:
    1. Fetch top headlines from NewsAPI
    2. Skip recently analyzed ones
    3. Run full VeritasAI pipeline on each
    4. Store results via feed_manager
    """
    logger.info("🕐 Trending cron job starting...")

    articles = await fetch_headlines()
    if not articles:
        logger.info("No articles to analyze")
        return

    fetched = len(articles)
    skipped = 0
    analyzed = 0
    errors = 0

    for article in articles:
        headline = article.get("title", "")
        description = article.get("description", "")
        url = article.get("url", "")

        if not headline or headline == "[Removed]":
            skipped += 1
            continue

        # Check if recently analyzed
        headline_hash = _md5(_normalize_text(headline))
        if await should_skip(headline_hash):
            skipped += 1
            logger.debug(f"Skipping (recently analyzed): {headline[:50]}...")
            continue

        try:
            # Combine headline + description for pipeline input
            input_text = headline
            if description and description != "[Removed]":
                input_text += f"\n\n{description}"

            # Run the full VeritasAI pipeline
            from routes.analyze import run_v2_pipeline
            result = await run_v2_pipeline(
                text=input_text,
                input_type="headline",
                content_type="news_report",
                source_type="auto_trending",
            )

            # Store via feed manager
            from lib.feed_manager import store_analysis
            await store_analysis(
                pipeline_result=result,
                source="auto_trending",
                headline=headline,
                source_url=url,
            )

            analyzed += 1
            logger.info(f"✅ Analyzed: {headline[:60]}...")

        except Exception as e:
            errors += 1
            logger.error(f"❌ Error analyzing '{headline[:50]}': {e}")
            continue

    logger.info(
        f"🕐 Trending cron complete: "
        f"fetched={fetched}, skipped={skipped}, analyzed={analyzed}, errors={errors}"
    )


def start_scheduler():
    """Start the APScheduler cron job. Call from FastAPI startup."""
    if not NEWS_API_KEY:
        logger.warning("NEWS_API_KEY not set — trending cron job will not start")
        return

    scheduler.add_job(
        run_trending_analysis,
        trigger='interval',
        hours=CRON_INTERVAL,
        id='trending_analysis',
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),  # Run immediately on startup
    )
    scheduler.start()
    logger.info(f"📅 Trending cron scheduled: every {CRON_INTERVAL} hours")
