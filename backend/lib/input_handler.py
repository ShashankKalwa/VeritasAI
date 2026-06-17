"""
VeritasAI v2 — Input Handler
Step 2: Input normalization + content_type detection.

Accepts: URL, raw article text, headline, social media post text.
Normalizes whitespace/encoding.
Detects or accepts explicit content_type:
    "news_report" | "opinion_satire" | "social_media_post"
"""
import os
import re
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Domains that indicate social media content
SOCIAL_DOMAINS = {
    "twitter.com", "x.com", "instagram.com", "facebook.com",
    "tiktok.com", "reddit.com", "threads.net",
}

# Known satire domains
SATIRE_DOMAINS = {
    "theonion.com", "babylonbee.com", "clickhole.com",
    "borowitz-report.newyorker.com", "fakingnews.firstpost.com",
    "newsthump.com", "waterfordwhispersnews.com",
}

# Opinion/first-person markers
OPINION_PATTERNS = [
    re.compile(r"\b(i think|i believe|in my (view|opinion)|my take|from my perspective)\b", re.I),
    re.compile(r"^(opinion|editorial|op-?ed|commentary)\s*[:\|—]", re.I),
]


async def normalize(text: str, input_type: str = "text", content_type: str = "auto") -> dict:
    """
    Normalize input text and detect content type.

    Args:
        text: Raw input text or URL.
        input_type: One of "url", "text", "headline", "social_post".
        content_type: One of "auto", "news_report", "opinion_satire", "social_media_post".

    Returns:
        dict with keys: text, input_type, content_type, original_url.
    """
    original_url = None

    # If input_type is URL, extract text from the URL first
    if input_type == "url" or _looks_like_url(text):
        original_url = text.strip()
        input_type = "url"
        from lib.file_parser import extract_text_from_url
        extracted = extract_text_from_url(original_url)
        if extracted:
            text = extracted
        else:
            # Fall back to treating URL as-is text (headline mode)
            logger.warning(f"Could not extract text from URL: {original_url}")

    # Normalize whitespace and encoding
    text = _normalize_text(text)

    # Detect content type if set to auto
    if content_type == "auto" or not content_type:
        content_type = detect_content_type(text, original_url)

    # Map social_post input type to content_type
    if input_type == "social_post" and content_type == "news_report":
        content_type = "social_media_post"

    return {
        "text": text,
        "input_type": input_type,
        "content_type": content_type,
        "original_url": original_url,
    }


def _looks_like_url(text: str) -> bool:
    """Check if the input text is a URL."""
    text = text.strip()
    if text.startswith(("http://", "https://", "www.")):
        return True
    # Check if it's a bare domain (e.g., "reuters.com/article/...")
    try:
        parsed = urlparse(text if "://" in text else f"https://{text}")
        return bool(parsed.netloc and "." in parsed.netloc and " " not in text)
    except Exception:
        return False


def _normalize_text(text: str) -> str:
    """Normalize whitespace, encoding, and clean up text."""
    if not text:
        return ""
    # Normalize unicode
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    # Collapse multiple whitespace (but preserve paragraph breaks)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return text.strip()


def detect_content_type(text: str, url: str = None) -> str:
    """
    Auto-detect content type from text and URL heuristics.

    Rules:
        - Social: starts with @, contains #hashtag, or is from social media domain.
        - Opinion/Satire: domain in known satire list, or heavy first-person + opinion markers.
        - Default: news_report.

    Returns: "news_report" | "opinion_satire" | "social_media_post"
    """
    # Check URL-based signals first
    if url:
        try:
            domain = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
            domain = domain.removeprefix("www.")
            if domain in SOCIAL_DOMAINS:
                return "social_media_post"
            if domain in SATIRE_DOMAINS:
                return "opinion_satire"
        except Exception:
            pass

    # Check text-based social signals
    if text:
        # Social media patterns
        if text.lstrip().startswith("@"):
            return "social_media_post"
        hashtag_count = len(re.findall(r"#\w+", text))
        if hashtag_count >= 2:
            return "social_media_post"

        # Opinion/satire patterns
        for pattern in OPINION_PATTERNS:
            if pattern.search(text):
                return "opinion_satire"

        # Satire markers in text
        if re.search(r"\b(satire|parody|not\s+real\s+news)\b", text, re.I):
            return "opinion_satire"

    return "news_report"
