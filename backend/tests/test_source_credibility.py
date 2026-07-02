import pytest
from lib.source_credibility import score_evidence

# Assuming backend/config/source_credibility.json has "reuters.com": 95
# If it's not present, we can mock _load_config, but let's test the public API first.

def test_score_evidence_known_domain(monkeypatch):
    # Mock config to be fully deterministic
    mock_config = {
        "domains": {"reuters.com": 95},
        "__known_lowquality__": [],
        "__default__": 40
    }
    import lib.source_credibility as sc
    monkeypatch.setattr(sc, "_load_config", lambda: mock_config)

    evidence = [{"url": "https://www.reuters.com/article/123"}]
    scored = score_evidence(evidence)
    
    assert scored[0]["credibility_score"] == 95
    assert scored[0]["source_domain"] == "reuters.com"

def test_score_evidence_unknown_domain(monkeypatch):
    mock_config = {
        "domains": {"reuters.com": 95},
        "__known_lowquality__": [],
        "__default__": 40
    }
    import lib.source_credibility as sc
    monkeypatch.setattr(sc, "_load_config", lambda: mock_config)

    evidence = [{"url": "https://unknown-random-blog.com/post"}]
    scored = score_evidence(evidence)
    
    assert scored[0]["credibility_score"] == 40
    assert scored[0]["source_domain"] == "unknown-random-blog.com"

def test_score_evidence_www_stripping(monkeypatch):
    mock_config = {
        "domains": {"nytimes.com": 90},
        "__known_lowquality__": [],
        "__default__": 40
    }
    import lib.source_credibility as sc
    monkeypatch.setattr(sc, "_load_config", lambda: mock_config)

    evidence = [{"url": "https://www.nytimes.com/world"}]
    scored = score_evidence(evidence)
    
    assert scored[0]["credibility_score"] == 90
    assert scored[0]["source_domain"] == "nytimes.com"

def test_five_low_cred_vs_one_high_cred(monkeypatch):
    """
    5 low-credibility sources don't outweigh 1 high-credibility source when summed.
    This asserts the core design claim of the project.
    """
    mock_config = {
        "domains": {"reuters.com": 95},
        "__known_lowquality__": ["fakeblog.com", "spam.com"],
        "__known_lowquality_score__": 12,
        "__default__": 40
    }
    import lib.source_credibility as sc
    monkeypatch.setattr(sc, "_load_config", lambda: mock_config)

    high_evidence = [{"url": "https://reuters.com/1"}]
    low_evidence = [
        {"url": "https://fakeblog.com/1"},
        {"url": "https://fakeblog.com/2"},
        {"url": "https://spam.com/1"},
        {"url": "https://spam.com/2"},
        {"url": "https://spam.com/3"}
    ]

    scored_high = score_evidence(high_evidence)
    scored_low = score_evidence(low_evidence)

    high_sum = sum(e["credibility_score"] for e in scored_high)
    low_sum = sum(e["credibility_score"] for e in scored_low)

    assert high_sum == 95
    assert low_sum == 12 * 5  # 60
    assert high_sum > low_sum
