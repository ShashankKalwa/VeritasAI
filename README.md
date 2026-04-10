# VeritasAI — AI-Powered Fake News Detection

> **"See Through the Noise"** | AITHON 2025 — Problem Statement #2

VeritasAI is a multi-engine AI platform that instantly detects fake news using an ensemble of 4 detection engines, file upload support, and real-time analytics.

## 🧠 Detection Engines

| Engine | Technology | Purpose |
|--------|-----------|---------|
| **Heuristic NLP** | 60+ regex pattern rules | Linguistic, rhetorical & source credibility analysis |
| **HuggingFace BERT** | `jy46604790/Fake-News-Bert-Detect` | Pre-trained transformer fake news classifier |
| **ClaimBuster DeBERTa** | `whispAI/ClaimBuster-DeBERTaV2` | Claim worthiness scoring |
| **Google Fact Check** | Fact Check Tools API | Cross-references verified fact-checks |

All engines feed into a **weighted ensemble merger** for maximum accuracy.

## ✨ Features

- 🔍 **Multi-Engine Detection** — 4 AI engines analyze text simultaneously
- 📁 **File Upload** — PDF, DOCX, TXT support with content validation
- 📊 **Analytics Dashboard** — Real-time charts (Chart.js)
- 🔴 **Live Feed** — WebSocket-powered real-time community feed
- 📰 **Dataset Explorer** — 500 labeled headlines, searchable & filterable
- 🔐 **Auth** — Supabase Auth (email/password, JWT)
- ⚡ **Instant** — Sub-second detection, no waiting

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite + Chart.js |
| **Backend** | FastAPI (Python) + Uvicorn |
| **AI/ML** | HuggingFace Inference API, Custom NLP |
| **Database** | Supabase (PostgreSQL + Realtime + Auth) |
| **Styling** | Vanilla CSS (dark newsroom theme) |

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
# Create backend/.env (see Environment Variables below)
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
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_key
ALLOWED_ORIGINS=http://localhost:5173
HF_API_TOKEN=your_huggingface_token
CLAIMBUSTER_HF_MODEL=whispAI/ClaimBuster-DeBERTaV2
GOOGLE_FACTCHECK_API_KEY=your_google_factcheck_key
```

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analyze` | Analyze text (4-engine ensemble) |
| `POST` | `/api/analyze/file` | Upload & analyze PDF/DOCX/TXT |
| `GET` | `/api/stats` | Dashboard statistics |
| `GET` | `/api/feed` | Recent analyses feed |
| `GET` | `/api/dataset` | Paginated dataset with filters |
| `GET` | `/api/dataset/stats` | Dataset summary |
| `GET` | `/docs` | Swagger API documentation |
| `GET` | `/health` | Health check |

## 🌐 Deployment

| Component | Platform | Notes |
|-----------|----------|-------|
| **Frontend** | **Netlify** | Auto-deploy from GitHub, `netlify.toml` included |
| **Backend** | **Render** | Free tier, `Procfile` included |
| **Database** | **Supabase** | Already deployed, cloud PostgreSQL |

### Deploy Frontend to Netlify
1. Connect GitHub repo to Netlify
2. Build command: `npm run build`
3. Publish directory: `dist`
4. Add env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`

### Deploy Backend to Render
1. Create new Web Service → Connect GitHub repo
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add env vars from `backend/.env`

## 📁 Project Structure

```
VeritasAI/
├── src/                  # React frontend
│   ├── components/       # Navbar, ArticleInput, ResultCard, etc.
│   ├── pages/            # DetectPage, DashboardPage, DatasetPage
│   ├── lib/              # API client, Supabase, heuristics
│   └── context/          # Auth context
├── backend/              # FastAPI backend
│   ├── routes/           # analyze, stats, feed, dataset
│   ├── lib/              # ml_model, heuristics, file_parser
│   └── main.py           # App entry point
├── public/               # Static assets
└── index.html            # SPA entry
```

## 👥 Team

Built for **AITHON 2025** Hackathon

---

*VeritasAI — See Through the Noise* 🔍
