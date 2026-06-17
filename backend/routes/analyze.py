"""
VeritasAI Ensemble Analysis Engine v3.0
Multi-engine convergence scoring with 5-label verdict taxonomy.

Labels: CREDIBLE → MOSTLY_TRUE → MIXED → MOSTLY_FALSE → FALSE
"""
import os
import json
import logging
import asyncio
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from lib.input_handler import normalize_and_detect_type
from lib.claim_extractor import extract_claims
from lib.ml_model import claimbuster_score, bert_signal
from lib.heuristics import manipulation_signal_async
from lib.evidence_retriever import retrieve_evidence
from lib.source_credibility import score_evidence
from lib.evidence_reasoner import reason_claim
from lib.ensemble_verdict_v2 import compute_claim_verdict, compute_overall_verdict
from lib.explainability_formatter import format_explainability
from lib.supabase_client import get_supabase
from lib.file_parser import extract_text, is_meaningful_content

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "text", "md"}

class AnalyzeRequest(BaseModel):
    input_type: str
    content: str
    explicit_type: str | None = None

async def process_analysis(input_type: str, content: str, explicit_type: str = None) -> dict:
    text, content_type = normalize_and_detect_type(input_type, content, explicit_type)
    
    if len(text) < 10:
        raise HTTPException(400, "Text must be at least 10 characters")
        
    text = text[:5000]
    
    claims_task = asyncio.create_task(extract_claims(text, content_type))
    bert_task = asyncio.create_task(bert_signal(text))
    manip_task = asyncio.create_task(manipulation_signal_async(text))
    
    claims, bert_val, manip_val = await asyncio.gather(claims_task, bert_task, manip_task)
    
    if not claims:
        return {
            "overall_verdict": "Opinion / Not Fact-Checkable",
            "overall_confidence": 0,
            "content_type": content_type,
            "claims": [],
            "explainability": {
                "primary_signal": "No factual claims were found to verify.",
                "secondary_signals": [],
                "top_sources": []
            }
        }
        
    async def process_single_claim(claim):
        c_text = claim["claim_text"]
        
        cb_score = await claimbuster_score(c_text)
        if cb_score < 40.0:
            claim["verdict"] = "Opinion / Not Fact-Checkable"
            claim["confidence"] = 0
            claim["model_signals"] = {
                "bert_linguistic_signal": bert_val,
                "heuristic_manipulation_signal": manip_val
            }
            return claim
            
        evidence_items = await retrieve_evidence(c_text)
        evidence_items = score_evidence(evidence_items)
        
        reasoned = await reason_claim(c_text, evidence_items, bert_val, manip_val)
        
        claim["evidence"] = reasoned
        claim["model_signals"] = {
            "bert_linguistic_signal": bert_val,
            "heuristic_manipulation_signal": manip_val
        }
        
        verdict, confidence = compute_claim_verdict(claim)
        claim["verdict"] = verdict
        claim["confidence"] = confidence
        return claim

    tasks = [asyncio.create_task(process_single_claim(c)) for c in claims]
    processed_claims = await asyncio.gather(*tasks)
    
    o_verdict, o_confidence = compute_overall_verdict(processed_claims)
    
    resp = format_explainability(processed_claims, o_verdict, o_confidence, content_type)
    
    async def _store():
        try:
            sb = get_supabase()
            sb.table("analyses").insert({
                "input_text": text[:500],
                "verdict": o_verdict,
                "confidence": o_confidence,
                "analysis": resp["explainability"]["primary_signal"],
                "indicators": resp["explainability"]["secondary_signals"],
                "category": "General",
                "heuristic_score": manip_val,
                "is_public": True,
            }).execute()
        except Exception as e:
            logger.error(f"Supabase error: {e}")

    asyncio.create_task(_store())
    
    return resp

@router.post("/api/analyze")
async def analyze_endpoint(req: AnalyzeRequest):
    return await process_analysis(req.input_type, req.content, req.explicit_type)

@router.post("/api/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    ext = file.filename.lower().rsplit(".", 1)[-1] if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '.{ext}'. Use PDF, DOCX, or TXT.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Maximum 5MB.")
    if not content:
        raise HTTPException(400, "File is empty.")

    text = extract_text(file.filename, content)
    if not text or not text.strip():
        raise HTTPException(400, "Could not extract text from this file.")

    is_valid, reason = is_meaningful_content(text)
    if not is_valid:
        raise HTTPException(422, reason)

    return await process_analysis("text", text[:5000].strip(), "news_report")
