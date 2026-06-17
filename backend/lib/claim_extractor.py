"""
LLM-based claim extraction module.
"""
import os
import json
import uuid
import logging
import re
from google import genai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a fact-checking assistant. Your job is to extract the main
factual, checkable claims from a news article or text.

Rules:
- Extract only FACTUAL claims (things that can be verified with evidence).
- Do NOT extract opinions, predictions, or normative statements.
- Each claim must be atomic (one fact per claim) and self-contained
  (understandable without reading the full article).
- Maximum {MAX_CLAIMS} claims.
- Respond ONLY with a valid JSON array. No preamble, no explanation,
  no markdown fences. Start your response with [ and end with ].

Output format:
[
  {
    "claim_id": "<uuid>",
    "claim_text": "<self-contained factual claim>",
    "source_span": "<the original sentence(s) this came from>"
  }
]"""

USER_PROMPT = """Extract the main factual claims from the following text.
Content type: {content_type}

TEXT:
{article_text}"""

async def extract_claims(text: str, content_type: str) -> list[dict]:
    """
    Extract factual claims from the normalized text.
    
    Args:
        text: Normalized article text
        content_type: The detected or explicit content type
        
    Returns:
        A list of dictionaries representing the extracted claims.
    """
    api_key = os.environ.get("GOOGLE_AI_API_KEY")
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        logger.info("Stub: extract_claims returning hardcoded claims because GOOGLE_AI_API_KEY is missing")
        return [
            {
                "claim_id": str(uuid.uuid4()),
                "claim_text": "Lenovo unveiled a transparent laptop at MWC",
                "source_span": "Lenovo unveiled a transparent laptop at MWC"
            },
            {
                "claim_id": str(uuid.uuid4()),
                "claim_text": "Sample checkable claim 2",
                "source_span": "Original sentence 2"
            }
        ]

    try:
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("LLM_MODEL_EXTRACT", "gemini-2.5-flash")
        max_claims = os.environ.get("MAX_CLAIMS", "5")
        
        sys_prompt = SYSTEM_PROMPT.replace("{MAX_CLAIMS}", str(max_claims))
        user_prompt = USER_PROMPT.replace("{content_type}", content_type).replace("{article_text}", text)
        
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=[
                {"role": "user", "parts": [{"text": sys_prompt + "\n\n" + user_prompt}]}
            ],
            config={"temperature": 0.0}
        )
        
        raw = response.text.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        
        claims = json.loads(raw)
        
        for c in claims:
            if "claim_id" not in c or not c["claim_id"] or c["claim_id"] == "<uuid>":
                c["claim_id"] = str(uuid.uuid4())
                
        return claims[:int(max_claims)]
        
    except Exception as e:
        logger.error(f"Error extracting claims with Gemini: {e}")
        return []
