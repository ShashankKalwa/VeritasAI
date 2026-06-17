"""
Input normalization and content type detection.
"""
import logging
import re
from lib.file_parser import extract_text_from_url

logger = logging.getLogger(__name__)

def normalize_and_detect_type(input_type: str, content: str, explicit_type: str = None) -> tuple[str, str]:
    """
    Normalizes input text and detects its content type.
    
    Args:
        input_type: The type of input ('url', 'text', 'headline', 'social_post')
        content: The actual text or URL
        explicit_type: Optional explicit type from the user
        
    Returns:
        tuple containing (normalized_text, content_type)
    """
    if input_type == "url":
        text = extract_text_from_url(content)
    else:
        text = content
        
    text = text.strip()
    
    content_type = explicit_type
    
    if not content_type or content_type == "Auto-detect":
        content_type = _auto_detect_type(input_type, content, text)
        
    return text, content_type

def _auto_detect_type(input_type: str, raw_content: str, parsed_text: str) -> str:
    if input_type == "social_post":
        return "social_media_post"
        
    if input_type == "url":
        url_lower = raw_content.lower()
        if "twitter.com" in url_lower or "x.com" in url_lower or "instagram.com" in url_lower:
            return "social_media_post"
            
    if raw_content.startswith("@") or "#" in raw_content:
        if len(raw_content) < 500:
            return "social_media_post"
            
    satire_domains = ["theonion.com", "babylonbee.com", "clickhole.com", "dailycurrant.com", "borowitzreport.com"]
    if input_type == "url":
        url_lower = raw_content.lower()
        if any(domain in url_lower for domain in satire_domains):
            return "opinion_satire"
            
    text_lower = parsed_text.lower()
    opinion_markers = ["i think", "in my view", "in my opinion", "i believe", "it seems to me"]
    markers_found = sum(1 for marker in opinion_markers if marker in text_lower)
    
    if markers_found >= 2 or (markers_found >= 1 and len(parsed_text.split()) < 300):
        return "opinion_satire"
        
    return "news_report"
