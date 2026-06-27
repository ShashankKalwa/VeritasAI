"""
VeritasAI — FastAPI Backend v3.0
Retrieval-Augmented Misinformation Verification System
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

from routes.analyze import router as analyze_router
from routes.stats import router as stats_router
from routes.feed import router as feed_router
from routes.dataset import router as dataset_router
from routes.trending import router as trending_router
from lib.ml_model import get_hf_detector, get_claimbuster_hf, get_google_factcheck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 VeritasAI v3 backend starting...")
    logger.info("=" * 60)

    # Signal engines
    logger.info("✅ Heuristic NLP (60+ rules — manipulation detection)")

    hf = get_hf_detector()
    logger.info("✅ BERT Fake News (linguistic signal)" if hf.available else "⏭️ BERT: Skipped (no HF token)")

    cb = get_claimbuster_hf()
    logger.info("✅ ClaimBuster DeBERTaV2 (check-worthiness gate)" if cb.available else "⏭️ ClaimBuster: Skipped")

    gfc = get_google_factcheck()
    logger.info("✅ Google Fact Check API (evidence)" if gfc.available else "⏭️ Google FC: Skipped")

    # v2 pipeline components
    import os
    has_llm = bool(os.getenv("GOOGLE_AI_API_KEY", ""))
    has_search = bool(os.getenv("SEARCH_API_KEY", ""))
    logger.info("✅ Gemini LLM (claim extraction + reasoning)" if has_llm else "⏭️ Gemini LLM: Stub mode (no API key)")
    logger.info("✅ Tavily Search (evidence retrieval)" if has_search else "⏭️ Tavily Search: Stub mode (no API key)")

    active = 1 + (1 if hf.available else 0) + (1 if cb.available else 0) + (1 if gfc.available else 0)
    logger.info("=" * 60)
    logger.info(f"🔥 VeritasAI v3 ready — {active}/4 signal engines + {'LLM' if has_llm else 'stub'} + {'search' if has_search else 'stub'}")
    logger.info("📁 File upload: PDF, DOCX, TXT, URL supported")
    logger.info("=" * 60)

    # Pre-warm HF models in background (so first request is fast)
    import asyncio
    async def _warmup():
        try:
            warmup_text = "Test warmup text for model loading"
            tasks = []
            if hf.available:
                tasks.append(hf.predict(warmup_text))
            if cb.available:
                tasks.append(cb.check(warmup_text))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.info("🔥 HF models warmed up!")
        except Exception:
            pass
    asyncio.create_task(_warmup())

    # Start trending cron scheduler (Phase 8)
    try:
        from jobs.trending_cron import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning(f"Trending scheduler start failed: {e}")

    yield

    # Shutdown scheduler
    try:
        from jobs.trending_cron import scheduler
        if scheduler.running:
            scheduler.shutdown(wait=False)
    except Exception:
        pass
    logger.info("👋 Shutting down")


app = FastAPI(
    title="VeritasAI API",
    description="Retrieval-Augmented Misinformation Verification System",
    version="3.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, tags=["analyze"])
app.include_router(stats_router, tags=["stats"])
app.include_router(feed_router, tags=["feed"])
app.include_router(dataset_router, tags=["dataset"])
app.include_router(trending_router, tags=["trending"])


@app.get("/")
async def root():
    import os
    hf = get_hf_detector()
    cb = get_claimbuster_hf()
    gfc = get_google_factcheck()
    engines = {
        "heuristic_nlp": {"status": "active", "type": "manipulation_detection"},
        "huggingface_bert": {"status": "active" if hf.available else "inactive", "type": "linguistic_signal"},
        "claimbuster_deberta": {"status": "active" if cb.available else "inactive", "type": "check_worthiness_gate"},
        "google_factcheck": {"status": "active" if gfc.available else "inactive", "type": "evidence_source"},
        "gemini_llm": {"status": "active" if os.getenv('GOOGLE_AI_API_KEY') else "stub", "type": "claim_extraction_reasoning"},
        "tavily_search": {"status": "active" if os.getenv('SEARCH_API_KEY') else "stub", "type": "evidence_retrieval"},
    }
    active = sum(1 for e in engines.values() if e["status"] == "active")
    return {
        "name": "VeritasAI API",
        "version": "3.0.0",
        "status": "online",
        "pipeline": "retrieval-augmented claim-level verification",
        "engines": f"{active}/{len(engines)} active",
        "engine_details": engines,
        "features": ["claim_extraction", "evidence_retrieval", "source_credibility", "explainability", "file_upload", "url_analysis"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
