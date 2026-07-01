# VeritasAI - Comprehensive Project Context & Architecture

This document provides a highly detailed, comprehensive overview of the **VeritasAI** (v3.0) project. It is intended to serve as complete context for AI coding assistants and developers. It covers the system architecture, technology stack, database schema, data shapes, environment configuration, setup instructions, and the core 12-step verification pipeline.

---

## 1. Project Overview
**VeritasAI** is an advanced claim-level fact verification platform. Unlike tools that analyze entire articles at a surface level, VeritasAI extracts individual factual claims, retrieves real-time evidence for each claim, filters out non-factual opinions, and computes an explainable ensemble verdict using multiple linguistic and heuristic signals.

### Core Capabilities
- **Claim-level verification:** Verifies individual atomic claims using Gemini 2.5 Flash.
- **Evidence Retrieval:** Uses Tavily Search API (for real-time web search) and Google Fact Check API.
- **Live Feed & Trending:** Real-time WebSockets (`Supabase realtime`) stream newly analyzed articles. A scheduled backend cron job aggregates trending claims.
- **Source Credibility:** Weights retrieved evidence based on a custom JSON database of 50+ scored domains (0-100 scale), ignoring low-quality sources.
- **Explainability:** Provides users with primary signals, contradicting signals, and top sources.

---

## 2. Technology Stack

### Frontend (`/src`)
- **Framework:** React 19 + Vite 8
- **Styling:** Vanilla CSS (`index.css` for layout, `animations.css` for interactions/shimmer effects)
- **Routing:** React Router v7 (`App.jsx`)
- **Data/Realtime:** `supabase-js` for WebSocket subscriptions on the `analyzed_news` table.
- **Charts:** `chart.js` and `react-chartjs-2` for dashboard statistics.
- **Deployment:** Configured for Vercel/Netlify.

### Backend (`/backend`)
- **Framework:** FastAPI (Python 3.12+) running on Uvicorn.
- **Database:** Supabase (PostgreSQL).
- **AI/ML Orchestration:** 
  - *Gemini 2.5 Flash*: Used for Claim Extraction (identifying checkable facts).
  - *Gemini 3.1 Pro Preview*: Used for Evidence Reasoning (evaluating if retrieved text supports/contradicts a claim).
  - *whispAI/ClaimBuster-DeBERTaV2*: HuggingFace model used as a gate to filter out opinions from checkable facts.
  - *jy46604790/Fake-News-Bert-Detect*: HuggingFace model used for linguistic credibility signals (detecting sensationalism/bias).
- **External APIs:** Tavily Search, Google Fact Check Tools.
- **Job Scheduling:** APScheduler (for the `/jobs/trending_cron.py` job).
- **Rate Limiting:** SlowAPI (prevents abuse on analysis endpoints).
- **Scraping:** Trafilatura (for URL extraction).

---

## 3. Database Schema & Data Shapes

The Supabase PostgreSQL database contains two primary tables:

### A. `analyzed_news`
Stores the results of every analysis.
- `id` (UUID, primary key)
- `headline_hash` (String, unique hash to prevent duplicate reprocessing)
- `headline`, `input_text` (String)
- `content_type` (String: auto, article, social, url, etc.)
- `overall_verdict` (String, mapped to 7-level taxonomy)
- `overall_confidence` (Integer, 0-100)
- `view_count`, `reanalysis_count`, `upvotes`, `downvotes` (Integer)
- `created_at`, `last_analyzed_at` (Timestamp)
- `reasoning_summary` (String, LLM-generated summary of the findings)

#### JSONB Column: `claims`
An array of objects representing each extracted claim:
```json
[
  {
    "claim": "The FTC settlement deadline for Amazon is next month.",
    "claimbuster_score": 0.85,
    "verdict": "Likely True",
    "confidence": 80,
    "evidence": [
      {
        "url": "https://example.com/article",
        "title": "Amazon FTC deadline approaching",
        "content": "...",
        "credibility_score": 85,
        "stance": "SUPPORTS" // Or CONTRADICTS / UNCLEAR
      }
    ]
  }
]
```

#### JSONB Column: `explainability`
```json
{
  "primary_signal": "Strong supporting evidence from 3 highly credible sources.",
  "secondary_signals": [
    "No manipulative linguistic patterns detected.",
    "Matches known Google Fact Checks."
  ]
}
```

#### JSONB Column: `top_sources`
Array of `{ "domain": "reuters.com", "score": 95, "url": "..." }`

### B. `trending_claims`
Stores aggregated claims extracted from `analyzed_news` to identify viral misinformation.
- `id` (UUID, primary key)
- `claim_text` (String, unique)
- `verdict` (String)
- `confidence` (Integer)
- `check_count` (Integer, how many times this claim appeared across different articles)
- `last_seen_at`, `created_at` (Timestamp)
- `source_articles` (JSONB, array of `{ id, headline }`)

---

## 4. Verification Pipeline (12 Steps)

When a user submits content to `/api/analyze`, it goes through `backend/lib/ensemble_verdict_v2.py`:

1. **Input Handler (`input_handler.py`):** Normalizes URL/text. Extracts HTML content via Trafilatura.
2. **Claim Extractor (`claim_extractor.py`):** Gemini 2.5 Flash extracts atomic factual claims up to `MAX_CLAIMS` (default: 5).
3. **ClaimBuster Gate (`ml_model.py`):** DeBERTa model scores each claim. Claims below `CLAIMBUSTER_GATE_THRESHOLD` (default: 40) are flagged as opinions.
4. **Evidence Retrieval (`evidence_retriever.py`):** Tavily API & Google Fact Check API gather URLs for each valid claim.
5. **Aggregation:** Evidence is deduplicated by URL and sorted.
6. **Source Credibility (`source_credibility.py`):** URLs are matched against `backend/config/source_credibility.json` to assign a weight (0-100).
7. **BERT Linguistic Signal (`ml_model.py`):** Evaluates the article's overall tone for fake news patterns.
8. **Heuristics Signal (`heuristics.py`):** Runs 60+ regex rules to detect manipulation tactics (e.g., excessive capitalization, sensationalist keywords).
9. **Evidence Reasoning (`evidence_reasoner.py`):** Gemini 3.1 Pro Preview evaluates if retrieved text SUPPORTS or CONTRADICTS the claim.
10. **Ensemble Verdict (`ensemble_verdict_v2.py`):** Weights the signals to compute per-claim verdicts:
    - 50% Evidence (weighted by Source Credibility)
    - 20% Heuristics
    - 15% BERT linguistic signal
    - 15% ClaimBuster factuality score
11. **Explainability (`explainability_formatter.py`):** Packages the results into a human-readable JSON payload.
12. **Feed Storage (`feed_manager.py`):** Inserts results into `analyzed_news` and upserts `trending_claims` (fire-and-forget logic).

---

## 5. 7-Level Verdict Taxonomy

| Label | Color | Meaning |
|-------|-------|---------|
| 🟢 **Credible** | `#22c55e` | Strong evidence supporting the claims from high-credibility sources. |
| 🟢 **Likely True** | `#86efac` | Mostly supported, but some minor gaps in evidence. |
| 🟡 **Mixed / Misleading** | `#eab308` | Evidence is contradictory or the claim omits crucial context. |
| 🟠 **Likely False** | `#f97316` | Significant contradicting evidence found. |
| 🔴 **False** | `#ef4444` | Clearly contradicted by highly reliable evidence. |
| ⚪ **Insufficient Evidence**| `#94a3b8` | Not enough sources found to verify. |
| 🟣 **Opinion** | `#6366f1` | Not a factual claim (opinion, prediction, satire). |

---

## 6. Project Setup & Environment Variables

### Prerequisites
- Node.js 18+
- Python 3.12+

### Frontend (`.env`)
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```
**Start:** `npm install` && `npm run dev`

### Backend (`backend/.env`)
```env
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# API Keys
HF_API_TOKEN=your_huggingface_token
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key
GOOGLE_AI_API_KEY=your_gemini_api_key
SEARCH_API_KEY=your_tavily_key

# Model & Provider Config
CLAIMBUSTER_HF_MODEL=whispAI/ClaimBuster-DeBERTaV2
LLM_MODEL_EXTRACT=gemini-2.5-flash
LLM_MODEL_REASON=gemini-3.1-pro-preview
SEARCH_API_PROVIDER=tavily

# Pipeline Tunables
MAX_CLAIMS=5
MAX_EVIDENCE_PER_CLAIM=6
CLAIMBUSTER_GATE_THRESHOLD=40
SOURCE_CREDIBILITY_CONFIG_PATH=backend/config/source_credibility.json

# Live Feed Cron (Trending)
NEWS_API_KEY=your_newsapi_key
NEWS_API_PROVIDER=newsapi
NEWS_API_LANGUAGE=en
NEWS_API_PAGE_SIZE=10
FEED_CRON_INTERVAL_HOURS=3
FEED_SKIP_IF_ANALYZED_WITHIN_HOURS=12
```
**Start:** `python -m venv venv`, `venv\Scripts\activate`, `pip install -r requirements.txt`, `uvicorn main:app --reload`

---

## 7. Complete API Routes

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Main verification entrypoint. Expects JSON `{ "text": "...", "inputType": "url|text", "contentType": "auto" }` |
| `POST` | `/api/analyze/file` | File upload entrypoint. Accepts `multipart/form-data` (PDF, DOCX, TXT, MD). |
| `GET` | `/api/stats` | Returns global system statistics (total verified, average confidence). |
| `GET` | `/api/feed` | Returns the 10 most recent analyses from `analyzed_news`. |
| `GET` | `/api/dataset` | Returns paginated, filterable dataset of all verified news. |
| `GET` | `/api/dataset/stats` | Returns aggregations for dataset visualizations (verdict distribution, etc.). |
| `GET` | `/api/trending` | Returns top trending claims sorted by `check_count`. |
| `POST` | `/api/vote` | Accepts user thumbs-up/down feedback for an article ID. |
| `POST` | `/api/trending/refresh`| Manually triggers the APScheduler job to recalculate trending claims. |
| `GET` | `/health` | Simple `{ "status": "ok" }` health check. |

---

## 8. Directory Map
```
VeritasAI/
├── src/                  # React Frontend
│   ├── components/       # UI building blocks (ResultCard, CommunityFeed, etc.)
│   ├── pages/            # Page layouts (DetectPage, DashboardPage, etc.)
│   ├── lib/              # API wrappers and Supabase client
│   ├── animations.css    # Subtle CSS transitions and keyframes
│   └── index.css         # Main stylesheet
├── backend/              # FastAPI Backend
│   ├── routes/           # API endpoints (analyze, feed, trending, stats)
│   ├── lib/              # Pipeline modules (extractor, retriever, reasoner)
│   ├── jobs/             # Scheduled tasks (trending_cron)
│   └── config/           # Static config (source_credibility.json)
└── AI_CONTEXT.md         # This document
```
