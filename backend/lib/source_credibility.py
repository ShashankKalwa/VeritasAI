"""
VeritasAI v2 — Source Credibility Scorer
Step 8: Domain → credibility score lookup.

Loads backend/config/source_credibility.json and attaches
credibility_score to each evidence item based on its domain.

IMPORTANT: Do NOT simply count sources. Weight them.
    5 low-score blogs (score 20 each) = 100 total weight.
    1 Reuters article (score 95) = 95 weight.
    These are roughly equal.
"""
import os
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

DEFAULT_SCORE = 40
_config_cache = None


def _load_config() -> dict:
    """Load and cache the source credibility config."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config_path = os.getenv(
        "SOURCE_CREDIBILITY_CONFIG_PATH",
        "backend/config/source_credibility.json",
    )

    # Try multiple paths for flexibility
    candidates = [
        config_path,
        Path(__file__).parent.parent / "config" / "source_credibility.json",
    ]

    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
                logger.info(f"Loaded source credibility config from {path}")
                return _config_cache
        except FileNotFoundError:
            continue
        except Exception as e:
            logger.error(f"Error loading credibility config from {path}: {e}")
            continue

    logger.warning("Source credibility config not found — using defaults")
    _config_cache = {"domains": {}, "__default__": DEFAULT_SCORE}
    return _config_cache


def _extract_domain(url: str) -> str:
    """Extract and normalize domain from URL."""
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc.lower()
        domain = domain.removeprefix("www.")
        return domain
    except Exception:
        return ""


def _lookup_score(domain: str) -> int:
    """Look up credibility score for a domain."""
    config = _load_config()
    domains = config.get("domains", {})
    known_lq = config.get("__known_lowquality__", [])
    lq_score = config.get("__known_lowquality_score__", 12)
    default = config.get("__default__", DEFAULT_SCORE)

    if not domain:
        return default

    # Direct match
    if domain in domains:
        return domains[domain]

    # Check known low-quality list
    if domain in known_lq:
        return lq_score

    # Check .gov TLD pattern (any subdomain of a .gov domain)
    if ".gov" in domain:
        # Try matching the base .gov domain
        parts = domain.split(".")
        for i in range(len(parts)):
            candidate = ".".join(parts[i:])
            if candidate in domains:
                return domains[candidate]
        # Any .gov domain gets a baseline boost
        return max(default, 75)

    # Check if a parent domain matches (e.g., "tech.reuters.com" → "reuters.com")
    parts = domain.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[i:])
        if parent in domains:
            return domains[parent]
        if parent in known_lq:
            return lq_score

    return default


def score_evidence(evidence_items: list[dict]) -> list[dict]:
    """
    Attach credibility_score to each evidence item based on its source domain.

    Items that already have a credibility_score set (e.g., fact-check results)
    are left unchanged.

    Args:
        evidence_items: List of evidence item dicts with 'url' field.

    Returns:
        Same list with 'credibility_score' field added/updated.
    """
    for item in evidence_items:
        # Skip if already scored (e.g., fact-check items with pre-set scores)
        if item.get("is_factcheck") and item.get("credibility_score", 0) > 0:
            continue

        domain = _extract_domain(item.get("url", ""))
        item["credibility_score"] = _lookup_score(domain)
        item["source_domain"] = domain

    return evidence_items


def get_domain_score(domain: str) -> int:
    """Public API: get credibility score for a domain string."""
    domain = domain.lower().removeprefix("www.")
    return _lookup_score(domain)
