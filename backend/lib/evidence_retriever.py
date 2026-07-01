"""
VeritasAI v2 — Evidence Retriever
Steps 5–7: Search API + Google Fact Check + evidence aggregation.

Retrieves real-time evidence from trusted sources for each check-worthy claim.
"""
import os
import logging
from urllib.parse import urlparse
from lib import cache

logger = logging.getLogger(__name__)

MAX_EVIDENCE_PER_CLAIM = int(os.getenv("MAX_EVIDENCE_PER_CLAIM", "6"))


async def retrieve_evidence(claim_text: str) -> list[dict]:
    """
    Step 5: Query search provider (Tavily) for evidence on a claim.

    Returns list of evidence items (without credibility scores).
    On failure: returns empty list + logs warning. Never crashes.
    """
    api_key = os.getenv("SEARCH_API_KEY", "")
    provider = os.getenv("SEARCH_API_PROVIDER", "tavily")

    if not api_key:
        logger.warning("SEARCH_API_KEY not set — returning empty evidence")
        return []

    cached = cache.get_tavily(claim_text)
    if cached is not None:
        logger.info(f"Cache HIT (tavily): {claim_text[:50]}")
        return cached

    logger.info(f"Cache MISS (tavily): {claim_text[:50]}")
    results = []
    if provider == "tavily":
        results = await _tavily_search(claim_text, api_key)
    else:
        logger.warning(f"Unknown search provider: {provider}")

    cache.set_tavily(claim_text, results)
    return results


async def _tavily_search(claim_text: str, api_key: str) -> list[dict]:
    """Execute Tavily search and return evidence items."""
    try:
        from tavily import AsyncTavilyClient

        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query=claim_text,
            search_depth="basic",
            max_results=MAX_EVIDENCE_PER_CLAIM,
            include_answer=False,
        )

        results = response.get("results", [])
        evidence = []
        for r in results[:MAX_EVIDENCE_PER_CLAIM]:
            evidence.append({
                "source_name": _extract_source_name(r.get("url", "")),
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "published_date": r.get("published_date"),
                "snippet": r.get("content", "")[:300],
                "credibility_score": 0,  # Will be set by source_credibility.py
            })

        logger.info(f"Tavily: {len(evidence)} results for claim: {claim_text[:60]}...")
        return evidence

    except ImportError:
        logger.error("tavily-python not installed — run: pip install tavily-python")
        return []
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
        return []


async def retrieve_factcheck(claim_text: str) -> list[dict]:
    """
    Step 6: Query Google Fact Check API for existing fact-checks on a claim.

    Wraps existing GoogleFactChecker from ml_model.py.
    Treats fact-check results as high-credibility evidence (85-95).
    """
    try:
        from lib.ml_model import get_google_factcheck
        gfc = get_google_factcheck()
        if not gfc.available:
            return []

        cached = cache.get_factcheck(claim_text)
        if cached is not None:
            logger.info(f"Cache HIT (factcheck): {claim_text[:50]}")
            return cached

        result = await gfc.check(claim_text)
        if not result or not result.get("found"):
            cache.set_factcheck(claim_text, [])
            return []

        evidence = []
        # Known fact-checker organizations get higher credibility
        HIGH_CRED_PUBLISHERS = {"AFP", "Reuters", "AP", "Associated Press",
                                "PolitiFact", "FactCheck.org", "Snopes",
                                "Full Fact", "Alt News", "BOOM"}

        for claim_data in result.get("claims", []):
            publisher = claim_data.get("publisher", "Unknown")
            cred = 95 if publisher in HIGH_CRED_PUBLISHERS else 85

            evidence.append({
                "source_name": f"{publisher} (Fact Check)",
                "url": claim_data.get("url", ""),
                "title": f"Fact Check: {claim_data.get('text', '')[:100]}",
                "published_date": None,
                "snippet": f"Rating: {claim_data.get('rating', 'Unknown')} — "
                           f"Claimed by {claim_data.get('claimant', 'Unknown')}",
                "credibility_score": cred,
                "is_factcheck": True,  # Flag for special handling
            })

        cache.set_factcheck(claim_text, evidence)
        logger.info(f"Google Fact Check: {len(evidence)} matches")
        return evidence

    except Exception as e:
        logger.error(f"Fact check retrieval error: {e}")
        return []


def aggregate_evidence(
    search_results: list[dict],
    factcheck_results: list[dict],
) -> list[dict]:
    """
    Step 7: Deduplicate by URL, merge search + fact-check results,
    sort by published_date descending (most recent first).
    """
    seen_urls = set()
    combined = []

    # Fact-check results first (higher priority)
    for item in factcheck_results:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined.append(item)
        elif not url:
            combined.append(item)

    # Then search results
    for item in search_results:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            combined.append(item)

    # Sort by published_date descending (None dates go last)
    def sort_key(item):
        d = item.get("published_date")
        return d if d else ""

    combined.sort(key=sort_key, reverse=True)

    return combined[:MAX_EVIDENCE_PER_CLAIM]


def _extract_source_name(url: str) -> str:
    """Extract a human-readable source name from a URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        domain = domain.removeprefix("www.")
        # Clean up common patterns
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-2].capitalize() if parts[-2] not in ("co", "com") else parts[-3].capitalize() if len(parts) >= 3 else domain
        return domain
    except Exception:
        return "Unknown Source"
