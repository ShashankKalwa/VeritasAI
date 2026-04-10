"""
VeritasAI — FastAPI Backend
AI-Powered Fake News Detection Engine

Features:
- Ensemble detection (TF-IDF ML + Heuristic NLP)
- RESTful API with CORS
- Supabase integration
- Rate limiting
- ML model trained on startup from dataset
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

from routes.analyze import router as analyze_router
from routes.stats import router as stats_router
from routes.feed import router as feed_router
from routes.dataset import router as dataset_router
from lib.ml_model import get_classifier
from lib.supabase_client import get_supabase

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Train ML model on startup using dataset from Supabase."""
    logger.info("🚀 VeritasAI backend starting...")

    try:
        sb = get_supabase()
        logger.info("📊 Fetching training data from Supabase...")
        resp = sb.table("dataset").select("headline, label").execute()
        data = resp.data or []

        if len(data) > 0:
            headlines = [d["headline"] for d in data]
            labels = [d["label"] for d in data]
            classifier = get_classifier()
            success = classifier.train(headlines, labels)
            if success:
                logger.info(f"✅ ML model trained on {len(data)} samples")
            else:
                logger.warning("⚠️ ML model training failed, using heuristics only")
        else:
            logger.warning("⚠️ No training data found in dataset table")

    except Exception as e:
        logger.error(f"❌ Startup training error: {e}")
        logger.info("Continuing with heuristic engine only...")

    logger.info("✅ VeritasAI backend ready!")
    yield
    logger.info("👋 VeritasAI backend shutting down")


app = FastAPI(
    title="VeritasAI API",
    description="AI-Powered Fake News Detection Engine",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(analyze_router, tags=["analyze"])
app.include_router(stats_router, tags=["stats"])
app.include_router(feed_router, tags=["feed"])
app.include_router(dataset_router, tags=["dataset"])


@app.get("/")
async def root():
    classifier = get_classifier()
    return {
        "name": "VeritasAI API",
        "version": "1.0.0",
        "status": "online",
        "ml_model_trained": classifier.is_trained,
        "engine": "ensemble (TF-IDF + Heuristic NLP)",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
