# VeritasAI — Retrieval-Augmented Misinformation Verification (v3.0)

> **"See Through the Noise"** — Claim-level fact verification with evidence retrieval, automated trending, and explainable AI.

VeritasAI is an advanced AI platform that verifies claims in news articles by extracting checkable claims, retrieving real-time evidence from credible sources, computing ensemble NLP/ML signals, and producing explainable, evidence-based verdicts.

## 🔬 Verification Pipeline (v3)

| Step | Component | Technology | Purpose |
|------|-----------|-----------|---------|
| 1-2 | **Input Handler** | Trafilatura + heuristics | URL/text extraction, content type detection |
| 3 | **Claim Extractor** | Gemini 2.5 Flash | Extract atomic, checkable factual claims |
| 4 | **ClaimBuster Gate** | `whispAI/ClaimBuster-DeBERTaV2` | Filter opinions from checkable facts (0% weight) |
| 5 | **Evidence Retrieval** | Tavily Search API | Real-time web search for each claim |
| 6 | **Google Fact Check** | Fact Check Tools API | Cross-reference verified fact-checks |
| 7 | **Aggregation** | Custom | Deduplicate, merge, sort evidence |
| 8 | **Source Credibility** | 50+ domain database | Score evidence sources (0-100) |
| 9a | **BERT Signal** | `jy46604790/Fake-News-Bert-Detect` | Linguistic credibility signal (15% weight) |
| 9b | **Heuristic Signal** | 60+ regex rules | Manipulation detection (20% weight) |
| 10 | **Evidence Reasoning** | Gemini 3.1 Pro Preview | Classify evidence as supporting/contradicting/unclear |
| 11 | **Ensemble Verdict** | Credibility-weighted | Per-claim + article verdict (50% evidence weight) |
| 12 | **Explainability** | Custom | Primary/secondary signals, top sources |

---

## ✨ Features

- 🧠 **Claim-Level Verification** — Extract and verify individual claims, not just article-level.
- 🌐 **Evidence Retrieval** — Real-time web search (Tavily) + Google Fact Check per claim.
- 📊 **Source Credibility** — 50+ domains scored and credibility-weighted (not simple source count).
- 💡 **Explainability** — Primary signal, supporting/contradicting signals, top sources.
- 📁 **Multi-Input** — URL, article text, headline, social post, or file upload (PDF/DOCX/TXT/MD).
- 📈 **Analytics Dashboard** — Real-time charts with 7-label verdict taxonomy.
- 🔴 **Live Feed** — WebSocket-powered community detection feed (recently analyzed articles).
- 🔥 **Trending Claims** — Aggregated database of trending claims sorted by check counts, updated automatically by an integrated background scheduler.
- 🛡️ **Rate Limiting & Quotas** — IP-based rate limits and daily API quotas powered by SlowAPI and Redis.
- ⚡ **Global Caching** — Upstash Redis caching for expensive LLM extractions and web searches.
- 🔄 **CI/CD Pipeline** — Automated testing via GitHub Actions on every push and pull request.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 + Vite 8 + Chart.js + React Router v7 |
| **Backend** | FastAPI (Python) + Uvicorn + SlowAPI (Rate Limiter) + APScheduler (Cron Jobs) |
| **AI/ML** | Gemini 2.5 Flash & 3.1 Pro Preview, HuggingFace, ClaimBuster DeBERTa |
| **Evidence** | Tavily Search API + Google Fact Check API + NewsAPI |
| **Database & Cache** | Supabase (PostgreSQL + Realtime) + Upstash Redis |
| **Styling** | Vanilla CSS (dark newsroom theme) |
| **CI/CD** | GitHub Actions |

---

## 🏷️ 7-Level Verdict Taxonomy

| Label | Color | Meaning |
|-------|-------|---------|
| 🟢 **Credible** | `#22c55e` | Strong evidence supporting the claims |
| 🟢 **Likely True** | `#86efac` | Mostly supported, minor gaps |
| 🟡 **Mixed / Misleading** | `#eab308` | Evidence is contradictory or partial |
| 🟠 **Likely False** | `#f97316` | Significant contradicting evidence |
| 🔴 **False** | `#ef4444` | Clearly contradicted by reliable evidence |
| ⚪ **Insufficient Evidence** | `#94a3b8` | Not enough sources found to verify |
| 🟣 **Opinion / Not Fact-Checkable** | `#6366f1` | Not a factual claim (opinion, prediction) |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+

### Frontend
```bash
npm install
npm run dev
# → http://localhost:5173
```

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
# Create backend/.env from backend/.env.example
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# → http://localhost:8000 (API)
# → http://localhost:8000/docs (Swagger)
```

---

## 🐳 Run Backend with Docker

```bash
cp backend/.env.example backend/.env
# Fill in your API keys

docker-compose up --build
# Backend → http://localhost:8000
# Backend docs → http://localhost:8000/docs
```

The frontend is deployed via Vercel and runs locally with `npm run dev`
as usual — it is not containerized.

---

## 🔑 Environment Variables

### Frontend (`.env`)
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```env
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Signal engines
HF_API_TOKEN=your_huggingface_token
CLAIMBUSTER_HF_MODEL=whispAI/ClaimBuster-DeBERTaV2
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key

# v3: LLM (claim extraction + reasoning)
GOOGLE_AI_API_KEY=your_gemini_api_key
LLM_MODEL_EXTRACT=gemini-2.5-flash
LLM_MODEL_REASON=gemini-2.5-pro

# ── v3: Evidence retrieval ──
SEARCH_API_PROVIDER=tavily
SEARCH_API_KEY=your_tavily_key

# ── v3: Pipeline config ──
MAX_CLAIMS=5
MAX_EVIDENCE_PER_CLAIM=6
CLAIMBUSTER_GATE_THRESHOLD=40
SOURCE_CREDIBILITY_CONFIG_PATH=backend/config/source_credibility.json

# ── v4: Redis Cache (Upstash) ──
UPSTASH_REDIS_URL=your_upstash_redis_url
UPSTASH_REDIS_TOKEN=your_upstash_redis_token
CACHE_TAVILY_TTL=21600
CACHE_FACTCHECK_TTL=43200
CACHE_HF_TTL=86400
CACHE_EXTRACTION_TTL=86400

# ── v4: Rate Limiting & Admin ──
UPSTASH_REDIS_PROTOCOL_URL=rediss://default:your_password@your_endpoint:6379
ADMIN_API_KEY=your_admin_api_key
DAILY_LIMIT_ANALYZE=200

# ── Live Feed Cron (Trending) ──
NEWS_API_KEY=your_newsapi_key
NEWS_API_PROVIDER=newsapi
NEWS_API_LANGUAGE=en
NEWS_API_PAGE_SIZE=10
FEED_CRON_INTERVAL_HOURS=3
FEED_SKIP_IF_ANALYZED_WITHIN_HOURS=12
```

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Verify text claims (v3 ensemble pipeline) |
| `POST` | `/api/analyze/file` | Upload & analyze PDF/DOCX/TXT/MD |
| `GET` | `/api/stats` | Dashboard global statistics |
| `GET` | `/api/feed` | Recent analyses feed (from analyzed_news) |
| `GET` | `/api/dataset` | Paginated dataset with filters |
| `GET` | `/api/dataset/stats` | Dataset statistics |
| `GET` | `/api/trending` | Trending claims sorted by check count |
| `POST` | `/api/trending/refresh` | Manually trigger trending claims scheduler job |
| `GET` | `/health` | API health check |
| `GET` | `/docs` | Swagger API documentation |

---

## 🤖 For AI Assistants & Developers

If you are an AI coding assistant, an LLM, or a developer looking to understand the deepest technical details of VeritasAI (including full database schemas, JSONB structures, and the complete data flow of the 12-step pipeline), please read the **[AI_CONTEXT.md](AI_CONTEXT.md)** file in the root directory. It serves as a comprehensive system prompt and architecture guide.

---

## 📁 Project Structure

```
VeritasAI/
├── src/                  # React frontend
│   ├── components/       # UI Components
│   │   ├── ArchDiagram.jsx         # Verification pipeline architecture visualizer
│   │   ├── ArticleInput.jsx        # File upload & text submission form
│   │   ├── AuthModal.jsx           # User authentication dialog
│   │   ├── CommunityFeed.jsx       # Recent verification stream
│   │   ├── LiveFeedTicker.jsx      # Bottom ticker showing latest claims
│   │   ├── MetricCard.jsx          # Statistics display card
│   │   ├── Navbar.jsx              # Navigation header
│   │   ├── ResultCard.jsx          # Verdict & evidence explainability details
│   │   └── TrendingClaimCard.jsx   # List item card for trending claims
│   ├── pages/            # Application Pages
│   │   ├── AboutPage.jsx           # Details about the project methodology
│   │   ├── DashboardPage.jsx       # Verification analytics & statistics charts
│   │   ├── DatasetPage.jsx         # Queryable, filtered database of verified news
│   │   ├── DetectPage.jsx          # Core analysis input and results area
│   │   └── FeedPage.jsx            # Trending claims page
│   ├── lib/              # Frontend utilities
│   │   ├── api.js                  # Axios wrapper for FastAPI
│   │   ├── heuristics.js           # Client-side validation
│   │   └── supabase.js             # Supabase client instantiation
│   ├── App.jsx           # Router configuration
│   └── main.jsx          # SPA entry point
├── backend/              # FastAPI backend
│   ├── routes/           # Router modules
│   │   ├── analyze.py              # Main verification pipeline routes
│   │   ├── dataset.py              # Paginated database query routes
│   │   ├── feed.py                 # Live feed retrieval routes
│   │   ├── stats.py                # Statistics aggregation routes
│   │   └── trending.py             # Trending claims routes
│   ├── lib/              # Verification & ML pipeline modules
│   │   ├── claim_extractor.py      # LLM claim extraction engine
│   │   ├── ensemble_verdict_v2.py  # Credibility-weighted verdict calculator
│   │   ├── evidence_reasoner.py    # LLM evidence reasoning evaluator
│   │   ├── evidence_retriever.py   # Tavily & Google FC evidence gatherer
│   │   ├── explainability_formatter.py # Response packaging and aggregation
│   │   ├── feed_manager.py         # Handles feed storage and retrieval logic
│   │   ├── file_parser.py          # Extractor for PDF/DOCX/TXT/URL inputs
│   │   ├── heuristics.py           # Regex-based NLP manipulation rules (60+ rules)
│   │   ├── input_handler.py        # Normalizes URL, headlines, text inputs
│   │   ├── ml_model.py             # HuggingFace BERT & ClaimBuster wrappers
│   │   ├── source_credibility.py   # Domain scoring & credential ranking
│   │   └── supabase_client.py      # Supabase wrapper
│   ├── config/           # Database & config files
│   │   └── source_credibility.json # 50+ pre-evaluated credibility scores
│   ├── jobs/             # Scheduled tasks
│   │   └── trending_cron.py        # Background scheduler for trending claims
│   ├── migrations/       # DB migration scripts
│   ├── main.py           # FastAPI server entry point
│   └── requirements.txt  # Python dependencies
├── public/               # Static assets
└── index.html            # HTML shell
```

---

## 👥 Team

*VeritasAI — See Through the Noise* 🔍
