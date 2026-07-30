"""
VeritasAI v2 — Explainability Formatter
Step 12: Structures the final API response with human-readable explanations.

Assembles:
    - primary_signal: one-line explanation of the dominant verdict factor
    - secondary_signals: list of supporting one-liners
    - top_sources: top 3 sources by credibility_score
"""
import logging

logger = logging.getLogger(__name__)


def format_response(
    claims: list[dict],
    overall_verdict: str,
    overall_confidence: float | None,
    content_type: str,
    text: str = "",
) -> dict:
    """
    Assemble the final structured v2 API response.

    Args:
        claims: List of processed claim dicts with verdicts, evidence, reasoning.
        overall_verdict: The article-level verdict label.
        overall_confidence: The article-level confidence (0-100 or None).
        content_type: Detected content type string.
        text: Original input text.

    Returns:
        Full v2 API response dict matching the api_contract spec.
    """
    # Build explainability
    primary, secondaries = _build_signals(claims, overall_verdict)
    top_sources = _build_top_sources(claims)

    # Format claims for response
    formatted_claims = []
    for c in claims:
        reasoning = c.get("reasoning", {})
        formatted_claims.append({
            "claim_id": c.get("claim_id", ""),
            "claim_text": c.get("claim_text", ""),
            "check_worthy": c.get("check_worthy", True),
            "claimbuster_score": c.get("claimbuster_score", 0),
            "verdict": c.get("verdict", "Insufficient Evidence"),
            "confidence": c.get("confidence"),
            "evidence": {
                "supporting": reasoning.get("supporting_evidence", []),
                "contradicting": reasoning.get("contradicting_evidence", []),
                "unclear": reasoning.get("unclear_evidence", []),
            },
            "reasoning": reasoning.get("reasoning"),
            "api_rate_limited": c.get("api_rate_limited", False),
            "model_signals": {
                "bert_linguistic_signal": c.get("bert_signal", 50),
                "heuristic_manipulation_signal": c.get("manipulation_signal", 50),
                "claimbuster_check_worthiness": c.get("claimbuster_score", 0),
                "google_factcheck_match": reasoning.get("google_factcheck_match", False),
                "google_factcheck_details": reasoning.get("google_factcheck_details"),
            },
        })

    has_rate_limit = any(c.get("api_rate_limited", False) for c in claims)

    return {
        "overall_verdict": overall_verdict,
        "overall_confidence": overall_confidence,
        "content_type": content_type,
        "claims": formatted_claims,
        "explainability": {
            "primary_signal": primary,
            "secondary_signals": secondaries,
            "top_sources": top_sources,
            "api_rate_limited": has_rate_limit,
        },
    }


def _build_signals(claims: list[dict], overall_verdict: str) -> tuple[str, list[str]]:
    """Build primary and secondary signal strings."""
    secondaries = []
    primary = ""

    # Collect all evidence across claims
    all_supporting = []
    all_contradicting = []
    has_factcheck = False

    for c in claims:
        reasoning = c.get("reasoning", {})
        all_supporting.extend(reasoning.get("supporting_evidence", []))
        all_contradicting.extend(reasoning.get("contradicting_evidence", []))
        if reasoning.get("google_factcheck_match"):
            has_factcheck = True

    # Primary signal — based on dominant factor
    if has_factcheck:
        primary = "Existing fact-check found from established fact-checking organization"
    elif all_supporting and not all_contradicting:
        # Get top source names
        top = sorted(all_supporting, key=lambda x: x.get("credibility_score", 0), reverse=True)
        names = list(dict.fromkeys(e.get("source_name", "Unknown") for e in top[:3]))
        if names:
            primary = f"Independent agreement from {', '.join(names)}"
        else:
            primary = "Multiple credible sources support the claims"
    elif all_contradicting and not all_supporting:
        top = sorted(all_contradicting, key=lambda x: x.get("credibility_score", 0), reverse=True)
        names = list(dict.fromkeys(e.get("source_name", "Unknown") for e in top[:3]))
        if names:
            primary = f"Contradicted by {', '.join(names)}"
        else:
            primary = "Multiple credible sources contradict the claims"
    elif all_supporting and all_contradicting:
        primary = "Evidence is mixed — some sources support while others contradict"
    elif overall_verdict == "Opinion / Not Fact-Checkable":
        primary = "Content classified as opinion or not containing fact-checkable claims"
    else:
        primary = "No credible sources found to verify or contradict the claims"

    # Secondary signals
    for c in claims:
        bert = c.get("bert_signal", 50)
        manip = c.get("manipulation_signal", 50)
        cb = c.get("claimbuster_score", 0)

        if bert > 70:
            secondaries.append("BERT: Writing style consistent with credible reporting")
        elif bert < 30:
            secondaries.append("BERT: Writing style shows patterns associated with misinformation")

        if manip > 80:
            secondaries.append("No manipulation or clickbait detected")
        elif manip < 30:
            secondaries.append("Multiple manipulation signals detected in the text")

        if cb > 70:
            secondaries.append(f"ClaimBuster: {cb:.0f}% check-worthy")
        elif cb < 30:
            secondaries.append(f"ClaimBuster: Low check-worthiness ({cb:.0f}%)")

        break  # Only add signals once (for the article, not per claim)

    # Deduplicate
    secondaries = list(dict.fromkeys(secondaries))

    return primary, secondaries[:5]


def _build_top_sources(claims: list[dict]) -> list[str]:
    """Build top 3 sources by credibility score with stance."""
    all_evidence = []
    for c in claims:
        reasoning = c.get("reasoning", {})
        for e in reasoning.get("supporting_evidence", []):
            all_evidence.append((e, "Supporting"))
        for e in reasoning.get("contradicting_evidence", []):
            all_evidence.append((e, "Contradicting"))

    # Sort by credibility score
    all_evidence.sort(key=lambda x: x[0].get("credibility_score", 0), reverse=True)

    # Deduplicate by source name
    seen = set()
    top = []
    for e, stance in all_evidence:
        name = e.get("source_name", "Unknown")
        if name not in seen:
            seen.add(name)
            score = e.get("credibility_score", 0)
            top.append(f"{name} ({score}) — {stance}")
        if len(top) >= 3:
            break

    return top
