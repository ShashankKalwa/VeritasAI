import pytest
from lib.heuristics import heuristic_analyze, manipulation_signal, detect_content_type

def test_detect_content_type_satire():
    assert detect_content_type("This is clearly satire and not real news") == "SATIRE"
    assert detect_content_type("Economists are baffled by this new trend") == "SATIRE"

def test_detect_content_type_opinion():
    assert detect_content_type("Opinion: Why I think the new policy is flawed") == "OPINION"
    assert detect_content_type("I believe this is a terrible idea") == "OPINION"

def test_detect_content_type_breaking():
    assert detect_content_type("BREAKING: Major earthquake hits the coast") == "BREAKING"

def test_heuristic_analyze_false_signals():
    text = "The mainstream media is hiding the shocking truth about the new world order and 5g causes cancer. Wake up sheeple!!!"
    result = heuristic_analyze(text)
    assert result["verdict"] in ["FALSE", "MOSTLY_FALSE"]
    assert result["false_signal_count"] > 2
    assert result["heuristic_score"] > 30

def test_heuristic_analyze_credible_signals():
    text = "According to Reuters, a new study published in nature confirms that the clinical trial was successful, data shows."
    result = heuristic_analyze(text)
    assert result["verdict"] == "CREDIBLE"
    assert result["heuristic_score"] < -20

def test_manipulation_signal_mapping():
    # Test that heavy manipulation maps to a low score (near 0)
    text_false = "The mainstream media is hiding the shocking truth about the new world order and 5g causes cancer. Wake up sheeple!!!"
    sig_false = manipulation_signal(text_false)
    assert sig_false < 50.0

    # Test that highly credible maps to a high score (near 100)
    text_credible = "According to Reuters, a new study published in nature confirms that the clinical trial was successful."
    sig_credible = manipulation_signal(text_credible)
    assert sig_credible > 50.0

def test_heuristic_analyze_too_short():
    assert heuristic_analyze("short") is None
