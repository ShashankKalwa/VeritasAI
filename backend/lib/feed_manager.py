"""
VeritasAI — Feed Manager
Stores analysis results into analyzed_news and upserts trending_claims.
Used by both /api/analyze (organic) and trending_cron (auto).
"""
import hashlib
import re
import json
import logging
from datetime import datetime, timezone
from lib.supabase_client import get_supabase

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Normalize text for hashing: lowercase, strip punctuation/whitespace."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _md5(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def _build_reasoning_summary(result: dict) -> str:
    """Build a 1-2 sentence reasoning summary from the pipeline result."""
    explainability = result.get("explainability", {})
    primary = explainability.get("primary_signal", "")
    verdict = result.get("overall_verdict", "Insufficient Evidence")
    confidence = result.get("overall_confidence")

    if primary:
        summary = f"Verdict: {verdict}"
        if confidence is not None:
            summary += f" ({confidence}% confidence)"
        summary += f". {primary}."
        return summary

    return f"Verdict: {verdict}" + (f" ({confidence}% confidence)" if confidence else "")


def _extract_top_sources_structured(result: dict) -> list:
    """Extract top sources as structured dicts for the analyzed_news table."""
    explainability = result.get("explainability", {})
    raw_sources = explainability.get("top_sources", [])

    structured = []
    for src in raw_sources[:5]:
        if isinstance(src, str):
            # Parse "SourceName (score) — Stance" format
            parts = src.split(" — ")
            stance = parts[1] if len(parts) > 1 else "Unknown"
            name_score = parts[0]
            # Extract score from parentheses
            import re as _re
            match = _re.search(r'(.+?)\s*\((\d+)\)', name_score)
            if match:
                structured.append({
                    "source_name": match.group(1).strip(),
                    "credibility_score": int(match.group(2)),
                    "stance": stance,
                })
            else:
                structured.append({
                    "source_name": name_score.strip(),
                    "credibility_score": 0,
                    "stance": stance,
                })
        elif isinstance(src, dict):
            structured.append(src)

    return structured


async def store_analysis(pipeline_result: dict, source: str = "user_submitted", headline: str = "", source_url: str = "") -> None:
    """
    Store a pipeline result in analyzed_news and upsert claims into trending_claims.

    Args:
        pipeline_result: Full pipeline response dict
        source: 'user_submitted' or 'auto_trending'
        headline: Original headline text (if available, else uses first claim)
        source_url: Source URL (if available)
    """
    try:
        sb = get_supabase()

        # Determine headline text
        if not headline:
            claims = pipeline_result.get("claims", [])
            if claims:
                headline = claims[0].get("claim_text", "")[:200]
            else:
                headline = "Untitled analysis"

        # Normalize and hash
        normalized = _normalize_text(headline)
        headline_hash = _md5(normalized)

        # Build row data
        claims_data = pipeline_result.get("claims", [])
        top_sources = _extract_top_sources_structured(pipeline_result)
        reasoning_summary = _build_reasoning_summary(pipeline_result)

        row = {
            "headline": headline[:500],
            "headline_hash": headline_hash,
            "summary": reasoning_summary[:500] if reasoning_summary else None,
            "source_url": source_url or None,
            "analysis_source": source,
            "overall_verdict": pipeline_result.get("overall_verdict", "Insufficient Evidence"),
            "overall_confidence": pipeline_result.get("overall_confidence"),
            "content_type": pipeline_result.get("content_type", "news_report"),
            "claim_count": len(claims_data),
            "claims": claims_data,
            "explainability": pipeline_result.get("explainability"),
            "top_sources": top_sources,
            "reasoning_summary": reasoning_summary,
            "last_analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check if already exists
        existing = (
            sb.table("analyzed_news")
            .select("id, view_count, reanalysis_count")
            .eq("headline_hash", headline_hash)
            .limit(1)
            .execute()
        )

        news_id = None
        if existing.data:
            # Update existing row
            existing_row = existing.data[0]
            news_id = existing_row["id"]
            sb.table("analyzed_news").update({
                "view_count": existing_row["view_count"] + 1,
                "reanalysis_count": existing_row["reanalysis_count"] + 1,
                "last_analyzed_at": row["last_analyzed_at"],
                "overall_verdict": row["overall_verdict"],
                "overall_confidence": row["overall_confidence"],
                "claims": row["claims"],
                "explainability": row["explainability"],
                "top_sources": row["top_sources"],
                "reasoning_summary": row["reasoning_summary"],
            }).eq("id", news_id).execute()
            logger.info(f"Updated analyzed_news row {news_id} (view_count +1)")
        else:
            # Insert new row
            insert_resp = sb.table("analyzed_news").insert(row).execute()
            if insert_resp.data:
                news_id = insert_resp.data[0]["id"]
            logger.info(f"Inserted new analyzed_news row: {headline[:60]}...")

        # Upsert trending claims
        if news_id:
            await _upsert_trending_claims(sb, claims_data, news_id)

    except Exception as e:
        logger.error(f"Feed manager store error: {e}")


async def _upsert_trending_claims(sb, claims: list, news_id: str) -> None:
    """Upsert each claim into trending_claims."""
    for claim in claims:
        try:
            claim_text = claim.get("claim_text", "")
            if not claim_text or len(claim_text) < 10:
                continue

            claim_hash = _md5(_normalize_text(claim_text))
            verdict = claim.get("verdict", "Insufficient Evidence")
            confidence = claim.get("confidence")

            # Check existing
            existing = (
                sb.table("trending_claims")
                .select("id, check_count, verdict_history, news_ids, current_confidence")
                .eq("claim_hash", claim_hash)
                .limit(1)
                .execute()
            )

            if existing.data:
                row = existing.data[0]
                new_count = row["check_count"] + 1

                # Build verdict history (keep last 5)
                history = row.get("verdict_history") or []
                history.append({
                    "verdict": verdict,
                    "confidence": confidence,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                })
                history = history[-5:]

                # Update news_ids array
                news_ids = row.get("news_ids") or []
                if news_id not in news_ids:
                    news_ids.append(news_id)

                # Only update verdict if new confidence is higher
                update_data = {
                    "check_count": new_count,
                    "verdict_history": history,
                    "news_ids": news_ids,
                    "last_checked_at": datetime.now(timezone.utc).isoformat(),
                }

                existing_confidence = row.get("current_confidence") or 0
                if confidence and confidence > existing_confidence:
                    update_data["current_verdict"] = verdict
                    update_data["current_confidence"] = confidence

                sb.table("trending_claims").update(update_data).eq("id", row["id"]).execute()
            else:
                # Build supporting sources from claim evidence
                evidence = claim.get("evidence", {})
                supporting = evidence.get("supporting", [])
                sources = []
                for ev in supporting[:3]:
                    sources.append({
                        "name": ev.get("source_name", "Unknown"),
                        "url": ev.get("url", ""),
                        "credibility_score": ev.get("credibility_score", 0),
                    })

                sb.table("trending_claims").insert({
                    "claim_text": claim_text[:500],
                    "claim_hash": claim_hash,
                    "current_verdict": verdict,
                    "current_confidence": confidence,
                    "check_count": 1,
                    "supporting_sources": sources,
                    "verdict_history": [{
                        "verdict": verdict,
                        "confidence": confidence,
                        "checked_at": datetime.now(timezone.utc).isoformat(),
                    }],
                    "news_ids": [news_id],
                }).execute()

        except Exception as e:
            logger.error(f"Trending claim upsert error for '{claim_text[:40]}': {e}")
            continue


async def get_feed(limit: int = 20, offset: int = 0, source: str = "all", verdict: str = None) -> list:
    """Fetch analyzed news feed, newest first."""
    try:
        sb = get_supabase()
        query = (
            sb.table("analyzed_news")
            .select("id, headline, source_url, analysis_source, overall_verdict, "
                    "overall_confidence, content_type, claim_count, reasoning_summary, "
                    "top_sources, view_count, vote_true, vote_false, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
        )

        if source and source != "all":
            query = query.eq("analysis_source", source)
        if verdict:
            query = query.eq("overall_verdict", verdict)

        resp = query.execute()
        return resp.data or []
    except Exception as e:
        logger.error(f"Feed fetch error: {e}")
        return []


async def get_trending(limit: int = 20, offset: int = 0, verdict: str = None) -> list:
    """Fetch trending claims sorted by check_count DESC."""
    try:
        sb = get_supabase()
        query = (
            sb.table("trending_claims")
            .select("*")
            .order("check_count", desc=True)
            .limit(limit)
            .offset(offset)
        )

        if verdict:
            query = query.eq("current_verdict", verdict)

        resp = query.execute()
        return resp.data or []
    except Exception as e:
        logger.error(f"Trending fetch error: {e}")
        return []
