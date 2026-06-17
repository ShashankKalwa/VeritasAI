# VeritasAI — Retrieval-Augmented Misinformation Verification

> **"See Through the Noise"** — Claim-level fact verification with evidence retrieval and explainable AI

VeritasAI is an AI platform that verifies claims in news articles by extracting checkable claims, retrieving real-time evidence from credible sources, and producing explainable, evidence-based verdicts.

## 🔬 Verification Pipeline (v2)

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
| 10 | **Evidence Reasoning** | Gemini 2.5 Flash | Classify evidence as supporting/contradicting/unclear |
| 11 | **Ensemble Verdict** | Credibility-weighted | Per-claim + article verdict (50% evidence weight) |
| 12 | **Explainability** | Custom | Primary/secondary signals, top sources |

## ✨ Features

- 🧠 **Claim-Level Verification** — Extract and verify individual claims, not just article-level
- 🌐 **Evidence Retrieval** — Real-time web search + Google Fact Check per claim
- 📊 **Source Credibility** — 50+ domains scored, credibility-weighted (not source count)
- 💡 **Explainability** — Primary signal, supporting signals, top sources
- 📁 **Multi-Input** — URL, article text, headline, social post, file upload (PDF/DOCX/TXT)
- 📈 **Analytics Dashboard** — Real-time charts with 7-label verdict taxonomy
- 🔴 **Live Feed** — WebSocket-powered community detection feed

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite + Chart.js |
| **Backend** | FastAPI (Python) + Uvicorn |
| **AI/ML** | Gemini 2.5 Flash, HuggingFace, ClaimBuster DeBERTa |
| **Evidence** | Tavily Search API + Google Fact Check API |
| **Database** | Supabase (PostgreSQL + Realtime) |
| **Styling** | Vanilla CSS (dark newsroom theme) |

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
pip install -r requirements.txt
# Create backend/.env from backend/.env.example
python -m uvicorn main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000 (API)
# → http://localhost:8000/docs (Swagger)
```

## 🔑 Environment Variables

### Frontend (`.env`)
```
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_API_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```
# Supabase
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
ALLOWED_ORIGINS=http://localhost:5173

# Signal engines
HF_API_TOKEN=your_huggingface_token
CLAIMBUSTER_HF_MODEL=whispAI/ClaimBuster-DeBERTaV2
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key

# v2: LLM (claim extraction + reasoning)
GOOGLE_AI_API_KEY=your_gemini_api_key
LLM_MODEL_EXTRACT=gemini-2.5-flash
LLM_MODEL_REASON=gemini-2.5-flash

# v2: Evidence retrieval
SEARCH_API_PROVIDER=tavily
SEARCH_API_KEY=your_tavily_key

# v2: Pipeline config
MAX_CLAIMS=5
MAX_EVIDENCE_PER_CLAIM=6
CLAIMBUSTER_GATE_THRESHOLD=40
```

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Verify text claims (v2 pipeline) |
| `POST` | `/api/analyze/file` | Upload & analyze PDF/DOCX/TXT |
| `GET` | `/api/stats` | Dashboard statistics |
| `GET` | `/api/feed` | Recent analyses feed |
| `GET` | `/api/dataset` | Paginated dataset with filters |
| `GET` | `/api/dataset/stats` | Dataset summary |
| `GET` | `/docs` | Swagger API documentation |
| `GET` | `/health` | Health check |

## 📁 Project Structure

```
VeritasAI/
├── src/                  # React frontend
│   ├── components/       # Navbar, ArticleInput, ResultCard, CommunityFeed
│   ├── pages/            # DetectPage, DashboardPage, DatasetPage
│   └── lib/              # API client, Supabase, heuristics
├── backend/              # FastAPI backend
│   ├── routes/           # analyze, stats, feed, dataset
│   ├── lib/              # Pipeline modules (12 steps)
│   │   ├── input_handler.py        # Input normalization
│   │   ├── claim_extractor.py      # LLM claim extraction
│   │   ├── evidence_retriever.py   # Tavily + Google FC
│   │   ├── source_credibility.py   # Domain scoring (50+)
│   │   ├── evidence_reasoner.py    # LLM evidence reasoning
│   │   ├── ensemble_verdict_v2.py  # Credibility-weighted verdict
│   │   ├── explainability_formatter.py # Response assembly
│   │   ├── ml_model.py            # BERT + ClaimBuster wrappers
│   │   ├── heuristics.py          # 60+ manipulation rules
│   │   └── file_parser.py         # PDF/DOCX/TXT/URL extraction
│   ├── config/           # Source credibility database
│   ├── migrations/       # DB migration scripts
│   └── main.py           # App entry point
├── public/               # Static assets
└── index.html            # SPA entry
```

## 👥 Team

Built for **AITHON 2025** Hackathon

---

*VeritasAI — See Through the Noise* 🔍
