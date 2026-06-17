"""
Retrieval of credible sources (Search API + Google Fact Check).
"""
import os
import asyncio
import httpx
import logging
from lib.ml_model import get_google_factcheck

logger = logging.getLogger(__name__)

async def retrieve_evidence(claim_text: str) -> list[dict]:
    """
    Retrieve evidence for a given check-worthy claim using search provider
    and Google Fact Check API.
    
    Args:
        claim_text: The extracted claim text
        
    Returns:
        A list of evidence items.
    """
    max_evidence = int(os.environ.get("MAX_EVIDENCE_PER_CLAIM", "6"))
    evidence_list = []
    
    gfc_task = asyncio.create_task(_fetch_gfc(claim_text))
    search_task = asyncio.create_task(_fetch_tavily(claim_text))
    
    gfc_results, search_results = await asyncio.gather(gfc_task, search_task)
    
    evidence_list.extend(gfc_results)
    evidence_list.extend(search_results)
    
    seen_urls = set()
    deduped = []
    for item in evidence_list:
        if not item.get("url") or item["url"] in seen_urls:
            continue
        seen_urls.add(item["url"])
        deduped.append(item)
    
    def date_sort_key(x):
        return x.get("published_date") or ""
        
    deduped.sort(key=date_sort_key, reverse=True)
    
    return deduped[:max_evidence]

async def _fetch_gfc(claim_text: str) -> list[dict]:
    gfc = get_google_factcheck()
    res = await gfc.check(claim_text)
    results = []
    if res and res.get("found"):
        for cl in res.get("claims", []):
            publisher = cl.get("publisher", "Fact Checker")
            score = 95 if publisher.lower() in ["reuters", "afp", "ap", "associated press"] else 85
            results.append({
                "source_name": publisher,
                "url": cl.get("url", ""),
                "title": f"Fact Check: {cl.get('text', claim_text)}",
                "published_date": None,
                "snippet": f"Rating: {cl.get('rating', 'Unknown')}. Claimant: {cl.get('claimant', 'Unknown')}",
                "credibility_score": score
            })
    return results

async def _fetch_tavily(claim_text: str) -> list[dict]:
    api_key = os.environ.get("SEARCH_API_KEY")
    if not api_key or api_key == "TODO_your_tavily_key":
        logger.info("Stub: _fetch_tavily returning empty since SEARCH_API_KEY is missing")
        return []
        
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": claim_text,
                    "search_depth": "basic",
                    "include_answer": False,
                    "include_domains": [],
                    "exclude_domains": [],
                    "max_results": 5
                },
                timeout=8.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for res in data.get("results", []):
                    url = res.get("url", "")
                    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
                    results.append({
                        "source_name": domain,
                        "url": url,
                        "title": res.get("title", ""),
                        "published_date": res.get("published_date", None),
                        "snippet": res.get("content", "")
                    })
                return results
            else:
                logger.warning(f"Tavily search failed with status {resp.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching from Tavily: {e}")
        return []
