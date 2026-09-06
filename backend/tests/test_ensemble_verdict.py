import pytest
from lib.ensemble_verdict_v2 import compute_claim_verdict, compute_overall_verdict

def test_compute_claim_verdict_all_supporting():
    reasoning = {
        "supporting_evidence": [{"credibility_score": 90}, {"credibility_score": 80}],
        "contradicting_evidence": [],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(reasoning, bert_signal=100.0, manipulation_signal=100.0, google_factcheck_match=False)
    # Evidence score = 1.0
    # Final = (1.0 * 0.5) + (1.0 * 0.15) + (1.0 * 0.2) = 0.85
    assert result["verdict"] == "Credible"
    assert result["final_score"] > 0.65

def test_compute_claim_verdict_all_contradicting():
    reasoning = {
        "supporting_evidence": [],
        "contradicting_evidence": [{"credibility_score": 90}],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(reasoning, bert_signal=0.0, manipulation_signal=0.0, google_factcheck_match=False)
    # Evidence score = -1.0
    # Final = (-1.0 * 0.5) + (-1.0 * 0.15) + (-1.0 * 0.2) = -0.85
    assert result["verdict"] == "False"
    assert result["final_score"] < -0.65

def test_compute_claim_verdict_insufficient_evidence():
    reasoning = {
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "unclear_evidence": []
    }
    result = compute_claim_verdict(reasoning, bert_signal=50.0, manipulation_signal=50.0)
    assert result["verdict"] == "Insufficient Evidence"

def test_compute_overall_verdict_dominant_false():
    claims = [
        {"check_worthy": True, "verdict": "Credible", "final_score": 0.8, "confidence": 80},
        {"check_worthy": True, "verdict": "False", "final_score": -0.9, "confidence": 90},
    ]
    result = compute_overall_verdict(claims)
    assert result["overall_verdict"] == "False"

def test_compute_overall_verdict_weighted_average():
    claims = [
        {"check_worthy": True, "verdict": "Credible", "final_score": 0.8, "confidence": 80}, # weight 2 -> 1.6
        {"check_worthy": True, "verdict": "Mixed / Misleading", "final_score": 0.0, "confidence": 0}, # weight 1 -> 0
    ]
    result = compute_overall_verdict(claims)
    # avg = 1.6 / 3 = 0.533
    assert result["overall_verdict"] == "Likely True"
