"""
VeritasAI v2 — Claim Extractor
Step 3: LLM-based claim extraction from article text.

Uses Google Gemini to extract atomic, checkable factual claims.
Falls back to stub claims if GOOGLE_AI_API_KEY is missing.
"""
import os
import re
import json
import uuid
import logging

logger = logging.getLogger(__name__)

MAX_CLAIMS = int(os.getenv("MAX_CLAIMS", "5"))

# Exact prompt templates from spec — do not modify
SYSTEM_PROMPT = """You are a fact-checking assistant. Your job is to extract the main
factual, checkable claims from a news article or text.

Rules:
- Extract only FACTUAL claims (things that can be verified with evidence).
- Do NOT extract opinions, predictions, or normative statements.
- Each claim must be atomic (one fact per claim) and self-contained
  (understandable without reading the full article).
- Maximum {max_claims} claims.
- Respond ONLY with a valid JSON array. No preamble, no explanation,
  no markdown fences. Start your response with [ and end with ].

Output format:
[
  {{
    "claim_id": "<uuid>",
    "claim_text": "<self-contained factual claim>",
    "source_span": "<the original sentence(s) this came from>"
  }}
]"""

USER_PROMPT = """Extract the main factual claims from the following text.
Content type: {content_type}

TEXT:
{article_text}"""


def _get_stub_claims(text: str) -> list[dict]:
    """Return hardcoded test claims when LLM is unavailable."""
    # For short inputs (headlines), treat the whole text as one claim
    if len(text.split()) < 30:
        return [
            {
                "claim_id": str(uuid.uuid4()),
                "claim_text": text.strip(),
                "source_span": text.strip(),
            }
        ]
    # For longer texts, extract first two sentences as claims
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    claims = []
    for s in sentences[:2]:
        s = s.strip()
        if len(s) > 15:
            claims.append({
                "claim_id": str(uuid.uuid4()),
                "claim_text": s,
                "source_span": s,
            })
    if not claims:
        claims.append({
            "claim_id": str(uuid.uuid4()),
            "claim_text": text[:200].strip(),
            "source_span": text[:200].strip(),
        })
    return claims


async def extract_claims(
    text: str,
    content_type: str = "news_report",
    max_claims: int = None,
) -> list[dict]:
    """
    Extract factual, checkable claims from article text using Gemini LLM.

    Args:
        text: Normalized article text.
        content_type: "news_report" | "opinion_satire" | "social_media_post"
        max_claims: Override for MAX_CLAIMS env var.

    Returns:
        List of claim dicts with claim_id, claim_text, source_span.
    """
    mc = max_claims or MAX_CLAIMS
    api_key = os.getenv("GOOGLE_AI_API_KEY", "")

    if not api_key:
        logger.warning("GOOGLE_AI_API_KEY not set — using stub claims")
        return _get_stub_claims(text)

    try:
        from google import genai

        client = genai.Client(api_key=api_key)

        system = SYSTEM_PROMPT.format(max_claims=mc)
        user = USER_PROMPT.format(content_type=content_type, article_text=text[:3000])
        prompt = system + "\n\n" + user

        response = await client.aio.models.generate_content(
            model=os.getenv("LLM_MODEL_EXTRACT", "gemini-2.5-flash"),
            contents=[
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            config={"temperature": 0.0},
        )

        raw = response.text.strip()

        # Strip markdown fences if model adds them anyway
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*$", "", raw)
        raw = raw.strip()

        claims = json.loads(raw)

        if not isinstance(claims, list):
            logger.warning("LLM returned non-list — falling back to stub")
            return _get_stub_claims(text)

        # Validate and cap
        valid_claims = []
        for c in claims[:mc]:
            if isinstance(c, dict) and "claim_text" in c:
                if "claim_id" not in c:
                    c["claim_id"] = str(uuid.uuid4())
                if "source_span" not in c:
                    c["source_span"] = c["claim_text"]
                valid_claims.append(c)

        if not valid_claims:
            logger.warning("LLM returned no valid claims — falling back to stub")
            return _get_stub_claims(text)

        logger.info(f"Extracted {len(valid_claims)} claims via Gemini")
        return valid_claims

    except json.JSONDecodeError as e:
        logger.error(f"Claim extraction JSON parse error: {e}")
        return _get_stub_claims(text)
    except Exception as e:
        logger.error(f"Claim extraction error: {e}")
        return _get_stub_claims(text)
