"""
Domain credibility scoring.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

_credibility_cache = None

def _load_config():
    global _credibility_cache
    if _credibility_cache is not None:
        return _credibility_cache
        
    config_path = os.environ.get("SOURCE_CREDIBILITY_CONFIG_PATH", "backend/config/source_credibility.json")
    # Resolve relative to the backend root directory (which is parent of lib)
    if not os.path.isabs(config_path):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        config_path = os.path.join(os.path.dirname(base_dir), config_path)
        
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            _credibility_cache = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load credibility config from {config_path}: {e}")
        _credibility_cache = {}
        
    return _credibility_cache

def score_evidence(evidence_items: list[dict]) -> list[dict]:
    """
    Attach a credibility_score to each evidence item based on its domain.
    """
    config = _load_config()
    default_score = config.get("__default__", 40)
    low_quality = config.get("__known_lowquality__", [])
    low_quality_score = config.get("__known_lowquality_score__", 12)
    
    for item in evidence_items:
        if "credibility_score" in item and item["credibility_score"] > 0:
            continue
            
        url = item.get("url", "")
        if not url:
            item["credibility_score"] = default_score
            continue
            
        domain = url.split("//")[-1].split("/")[0].lower()
        domain = domain.replace("www.", "")
        
        score = None
        if domain in config and not domain.startswith("__"):
            score = config[domain]
        else:
            if domain.endswith(".gov") or ".gov." in domain:
                score = 90
            else:
                for lq in low_quality:
                    if lq in domain:
                        score = low_quality_score
                        break
                        
        item["credibility_score"] = score if score is not None else default_score
        
    return evidence_items
