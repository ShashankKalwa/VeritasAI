"""
Explainable report formatter.
"""
import logging

logger = logging.getLogger(__name__)

def format_explainability(claims: list[dict], overall_verdict: str, overall_confidence: int, content_type: str) -> dict:
    """
    Assemble the final structured API response.
    """
    all_evidence = []
    for c in claims:
        if "evidence" in c:
            all_evidence.extend(c["evidence"].get("supporting", []))
            all_evidence.extend(c["evidence"].get("contradicting", []))
            all_evidence.extend(c["evidence"].get("unclear", []))
            
    all_evidence.sort(key=lambda x: x.get("credibility_score", 0), reverse=True)
    seen_sources = set()
    top_sources = []
    for e in all_evidence:
        src = e.get("source_name", "")
        if src and src not in seen_sources:
            stance = e.get("stance", "unknown").capitalize()
            cred = e.get("credibility_score", 0)
            top_sources.append(f"{src} ({cred}) — {stance}")
            seen_sources.add(src)
        if len(top_sources) >= 3:
            break
            
    if overall_verdict == "False":
        primary_signal = "Strong evidence from credible sources contradicts the main claims."
    elif overall_verdict == "Credible":
        primary_signal = "Multiple high-credibility sources support the main claims."
    elif overall_verdict == "Likely True":
        primary_signal = "Evidence mostly supports the claims, with minor gaps."
    elif overall_verdict == "Likely False":
        primary_signal = "Evidence mostly contradicts the claims."
    elif overall_verdict == "Mixed / Misleading":
        primary_signal = "Evidence conflicts or the claims are misleadingly framed."
    elif overall_verdict == "Opinion / Not Fact-Checkable":
        primary_signal = "Content is primarily opinion or not fact-checkable."
    else:
        primary_signal = "No credible sources found to support or contradict the claim."
        
    secondary_signals = []
    if any(c.get("model_signals", {}).get("bert_linguistic_signal", 0) >= 80 for c in claims):
        secondary_signals.append("BERT: Writing style consistent with credible reporting")
    elif any(c.get("model_signals", {}).get("bert_linguistic_signal", 0) <= 30 for c in claims):
        secondary_signals.append("BERT: Writing style is characteristic of unreliable sources")
        
    if any(c.get("model_signals", {}).get("heuristic_manipulation_signal", 0) >= 80 for c in claims):
        secondary_signals.append("Heuristics: No manipulation or clickbait detected")
    elif any(c.get("model_signals", {}).get("heuristic_manipulation_signal", 0) <= 40 for c in claims):
        secondary_signals.append("Heuristics: Manipulation or sensationalism detected")

    return {
        "overall_verdict": overall_verdict,
        "overall_confidence": overall_confidence,
        "content_type": content_type,
        "claims": claims,
        "explainability": {
            "primary_signal": primary_signal,
            "secondary_signals": secondary_signals,
            "top_sources": top_sources
        }
    }
