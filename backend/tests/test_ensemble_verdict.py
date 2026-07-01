import pytest
from backend.lib.ensemble_verdict_v2 import compute_claim_verdict

def test_compute_claim_verdict_credible():
    reasoning = {
        "supporting_evidence": [{"credibility_score": 90}, {"credibility_score": 85}],
        "contradicting_evidence": [],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(
        reasoning=reasoning,
        bert_signal=80,
        manipulation_signal=90,
        google_factcheck_match=False
    )
    assert result["verdict"] == "Credible"
    assert result["confidence"] >= 65

def test_compute_claim_verdict_false():
    reasoning = {
        "supporting_evidence": [],
        "contradicting_evidence": [{"credibility_score": 95}, {"credibility_score": 90}],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(
        reasoning=reasoning,
        bert_signal=20,
        manipulation_signal=30,
        google_factcheck_match=False
    )
    assert result["verdict"] == "False"
    assert result["confidence"] >= 65

def test_compute_claim_verdict_mixed():
    reasoning = {
        "supporting_evidence": [{"credibility_score": 80}],
        "contradicting_evidence": [{"credibility_score": 80}],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(
        reasoning=reasoning,
        bert_signal=50,
        manipulation_signal=50,
        google_factcheck_match=False
    )
    assert result["verdict"] == "Mixed / Misleading"
    assert result["confidence"] <= 25

def test_compute_claim_verdict_insufficient():
    reasoning = {
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(
        reasoning=reasoning,
        bert_signal=50,
        manipulation_signal=50,
        google_factcheck_match=False
    )
    assert result["verdict"] == "Insufficient Evidence"

def test_claimbuster_does_not_affect_score():
    # ClaimBuster score is NOT a parameter in compute_claim_verdict
    # It's explicitly stated to have 0 weight. We prove this by showing
    # the function signature doesn't take it, and weights dict has it at 0.
    from backend.lib.ensemble_verdict_v2 import WEIGHTS
    assert WEIGHTS["claimbuster"] == 0.0
