"""
VeritasAI — FastAPI Backend v2.0
Multi-Engine Fake News Detection System
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
from lib.ml_model import get_hf_detector, get_claimbuster_hf, get_google_factcheck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 VeritasAI backend starting...")
    logger.info("=" * 60)

    # Engine 1: Heuristic (always on)
    logger.info("✅ Engine 1: Heuristic NLP (60+ rules)")

    # Engine 2: HF BERT Fake News
    hf = get_hf_detector()
    logger.info("✅ Engine 2: HF BERT Fake News" if hf.available else "⏭️ Engine 2: Skipped (no HF token)")

    # Engine 3: ClaimBuster DeBERTa
    cb = get_claimbuster_hf()
    logger.info("✅ Engine 3: ClaimBuster DeBERTaV2" if cb.available else "⏭️ Engine 3: Skipped")

    # Engine 4: Google Fact Check
    gfc = get_google_factcheck()
    logger.info("✅ Engine 4: Google Fact Check API" if gfc.available else "⏭️ Engine 4: Skipped")

    active = 1 + (1 if hf.available else 0) + (1 if cb.available else 0) + (1 if gfc.available else 0)
    logger.info("=" * 60)
    logger.info(f"🔥 VeritasAI ready — {active}/4 engines active")
    logger.info("📁 File upload: PDF, DOCX, TXT supported")
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

    yield
    logger.info("👋 Shutting down")


app = FastAPI(
    title="VeritasAI API",
    description="Multi-Engine AI Fake News Detection with File Upload Support",
    version="2.0.0",
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


@app.get("/")
async def root():
    hf = get_hf_detector()
    cb = get_claimbuster_hf()
    gfc = get_google_factcheck()
    engines = {
        "heuristic_nlp": {"status": "active", "type": "rule_engine"},
        "huggingface_bert": {"status": "active" if hf.available else "inactive", "type": "transformer"},
        "claimbuster_deberta": {"status": "active" if cb.available else "inactive", "type": "claim_detection"},
        "google_factcheck": {"status": "active" if gfc.available else "inactive", "type": "fact_check_api"},
    }
    active = sum(1 for e in engines.values() if e["status"] == "active")
    return {
        "name": "VeritasAI API",
        "version": "2.0.0",
        "status": "online",
        "engines": f"{active}/4 active",
        "engine_details": engines,
        "features": ["text_analysis", "file_upload", "multi_engine_ensemble", "google_factcheck"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
