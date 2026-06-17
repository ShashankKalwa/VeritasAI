"""
Ensemble verdict calculation V2.
"""
import logging

logger = logging.getLogger(__name__)

def compute_claim_verdict(claim: dict) -> tuple[str, int]:
    """
    Compute a per-claim verdict and confidence score based on the ensemble weights.
    """
    supp_ev = claim.get("evidence", {}).get("supporting", [])
    contr_ev = claim.get("evidence", {}).get("contradicting", [])
    unclear_ev = claim.get("evidence", {}).get("unclear", [])
    
    supp_sum = sum(e.get("credibility_score", 40) for e in supp_ev)
    contr_sum = sum(e.get("credibility_score", 40) for e in contr_ev)
    uncl_sum = sum(e.get("credibility_score", 40) for e in unclear_ev)
    
    total_cred = supp_sum + contr_sum + uncl_sum
    
    if total_cred == 0:
        return "Insufficient Evidence", 0
        
    evidence_score = (supp_sum - contr_sum) / max(total_cred, 1)
    
    models = claim.get("model_signals", {})
    bert = models.get("bert_linguistic_signal", 50.0)
    bert_mapped = (bert - 50.0) / 50.0
    
    manip = models.get("heuristic_manipulation_signal", 50.0)
    manip_mapped = (manip - 50.0) / 50.0
    
    gfc_val = 0.0
    for e in supp_ev:
        if "Fact Check:" in e.get("title", ""):
            gfc_val = 1.0
            break
    if gfc_val == 0.0:
        for e in contr_ev:
            if "Fact Check:" in e.get("title", ""):
                gfc_val = -1.0
                break
                
    final_score = (
        evidence_score * 0.50 +
        gfc_val * 0.15 +
        bert_mapped * 0.15 +
        manip_mapped * 0.20
    )
    
    final_score = max(-1.0, min(1.0, final_score))
    
    if final_score >= 0.65:
        verdict = "Credible"
    elif final_score >= 0.25:
        verdict = "Likely True"
    elif final_score > -0.25:
        verdict = "Mixed / Misleading"
    elif final_score > -0.65:
        verdict = "Likely False"
    else:
        verdict = "False"
        
    confidence = int(abs(final_score) * 100)
    confidence = max(0, min(100, confidence))
    
    return verdict, confidence

def compute_overall_verdict(claims: list[dict]) -> tuple[str, int]:
    """
    Derive the overall article verdict from the per-claim verdicts.
    """
    if not claims:
        return "Insufficient Evidence", 0
        
    valid_claims = [c for c in claims if c.get("verdict") not in ["Opinion / Not Fact-Checkable", "Insufficient Evidence"]]
    if not valid_claims:
        return "Opinion / Not Fact-Checkable", 0
        
    for c in valid_claims:
        if c.get("verdict") == "False" and c.get("confidence", 0) > 70:
            return "False", c.get("confidence", 0)
            
    total_weight = 0
    total_score = 0
    for idx, c in enumerate(valid_claims):
        v = c.get("verdict")
        conf = c.get("confidence", 0) / 100.0
        
        if v in ["Credible", "Likely True"]:
            score = conf
        elif v in ["Likely False", "False"]:
            score = -conf
        else:
            score = 0.0
            
        weight = max(1.0, float(len(valid_claims) - idx))
        total_score += score * weight
        total_weight += weight
        
    avg_score = total_score / total_weight if total_weight > 0 else 0
    
    if avg_score >= 0.65:
        verdict = "Credible"
    elif avg_score >= 0.25:
        verdict = "Likely True"
    elif avg_score > -0.25:
        verdict = "Mixed / Misleading"
    elif avg_score > -0.65:
        verdict = "Likely False"
    else:
        verdict = "False"
        
    confidence = int(abs(avg_score) * 100)
    return verdict, confidence
