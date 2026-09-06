import pytest
import os
import json
from unittest.mock import patch, mock_open
from lib.source_credibility import get_domain_score, score_evidence

@pytest.fixture
def mock_config():
    return {
        "domains": {
            "reuters.com": 95,
            "apnews.com": 95,
            "breitbart.com": 20
        },
        "__known_lowquality__": ["fake-news.xyz"],
        "__known_lowquality_score__": 15,
        "__default__": 40
    }

def test_get_domain_score_known(mock_config):
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        assert get_domain_score("reuters.com") == 95
        assert get_domain_score("apnews.com") == 95
        assert get_domain_score("tech.reuters.com") == 95 # Subdomain matching

def test_get_domain_score_low_quality(mock_config):
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        assert get_domain_score("fake-news.xyz") == 15

def test_get_domain_score_default(mock_config):
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        assert get_domain_score("unknown-blog.com") == 40

def test_get_domain_score_gov(mock_config):
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        assert get_domain_score("nih.gov") >= 75
        assert get_domain_score("some.state.gov") >= 75

def test_score_evidence(mock_config):
    evidence = [
        {"url": "https://www.reuters.com/article/1"},
        {"url": "http://unknown-blog.com/post"},
        {"url": "https://fake-news.xyz/conspiracy"}
    ]
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        scored = score_evidence(evidence)
        assert scored[0]["credibility_score"] == 95
        assert scored[1]["credibility_score"] == 40
        assert scored[2]["credibility_score"] == 15

def test_score_evidence_preserves_factcheck(mock_config):
    evidence = [
        {"url": "https://snopes.com/fact-check", "is_factcheck": True, "credibility_score": 99}
    ]
    with patch("lib.source_credibility._load_config", return_value=mock_config):
        scored = score_evidence(evidence)
        assert scored[0]["credibility_score"] == 99 # Not overwritten
