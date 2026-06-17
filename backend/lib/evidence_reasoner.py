"""
LLM evidence vs claim reasoning module.
"""
import os
import json
import logging
import re
from google import genai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an evidence analyst for a fact-verification system.
Given a factual claim and a list of evidence items retrieved from
credible sources, your job is to:
  1. Classify each evidence item as supporting, contradicting,
     or unclear relative to the claim.
  2. Write a 1–2 sentence reasoning summary explaining the overall
     picture.

Weighting guidance:
  - Higher credibility_score sources carry more weight in your reasoning.
  - A single Reuters/AP/BBC article (score 90+) outweighs several
    unknown blogs (score 40).
  - If evidence directly conflicts, say so — do not average it away.
  - If no evidence clearly addresses the claim, classify it as unclear
    and state that explicitly in the reasoning.

Respond ONLY with a valid JSON object. No preamble, no explanation,
no markdown fences. Start with { and end with }.

Output format:
{
  "supporting_evidence": [{"source_name": "...", "url": "...", "title": "...",
    "snippet": "...", "credibility_score": 0, "stance": "supporting"}],
  "contradicting_evidence": [...],
  "unclear_evidence": [...],
  "reasoning": "<1–2 sentence plain English summary>"
}"""

USER_PROMPT = """CLAIM: {claim_text}

EVIDENCE ITEMS:
{evidence_json}

ADDITIONAL SIGNALS:
- BERT linguistic credibility signal: {bert_signal}/100
  (100 = writing style strongly consistent with credible reporting)
- Heuristic manipulation signal: {manipulation_signal}/100
  (100 = no manipulation detected, 0 = heavy manipulation)

Classify each evidence item and provide your reasoning."""

async def reason_claim(claim_text: str, evidence: list[dict], bert_signal: float, manipulation_signal: float) -> dict:
    """
    Classify evidence items as supporting/contradicting/unclear and generate
    a reasoning summary.
    """
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        logger.info("Stub: reason_claim returning hardcoded output since GOOGLE_AI_API_KEY is missing")
        return {
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "unclear_evidence": evidence,
            "reasoning": "Missing API Key to perform reasoning."
        }
        
    try:
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("LLM_MODEL_REASON", "gemini-3.1-pro-preview")
        
        evidence_json = json.dumps(evidence, indent=2)
        user_prompt = USER_PROMPT.format(
            claim_text=claim_text,
            evidence_json=evidence_json,
            bert_signal=round(bert_signal, 1),
            manipulation_signal=round(manipulation_signal, 1)
        )
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=[
                {"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + user_prompt}]}
            ],
            config={"temperature": 0.1}
        )
        
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        
        return json.loads(raw)
        
    except Exception as e:
        logger.error(f"Error reasoning claim with Gemini: {e}")
        return {
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "unclear_evidence": evidence,
            "reasoning": "Error occurred during reasoning."
        }
