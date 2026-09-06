# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-09-06
### Added
- Upstash Redis global caching for expensive LLM extractions and web searches.
- IP-based rate limiting via SlowAPI to protect backend resources.
- Configurable daily API quotas (e.g. Gemini, Tavily, NewsAPI) to prevent budget exhaustion.
- Automated `keep_alive.py` cron jobs for Render, Supabase, and Upstash Redis.
- Comprehensive `pytest` test suite covering core verification logic, heuristics, and credibility scoring.
- Automated GitHub Actions CI workflow to run tests on every push.
- Project `LICENSE` and `CONTRIBUTING.md`.

### Fixed
- Gemini 429 rate limit issues during trending claims extraction by introducing staggered delays.
- Resolved persistent DNS resolution (`[Errno -5]`) and connection timeouts by replacing global `httpx` clients with scoped clients and adding smart retries.
- Lowered Hugging Face API fallback timeouts to fail-fast and avoid blocking the pipeline when community endpoints go offline.

## [3.0.0]
### Added
- RAG architecture integrating Tavily Search API and Google Fact Check Tools.
- 12-step verification pipeline powered by Gemini 2.5 Flash for extraction and 3.1 Pro Preview for reasoning.
- 7-level semantic verdict taxonomy (Credible, Likely True, Mixed, etc.).
- Credibility-weighted evidence aggregation based on 50+ domain scores.
- Automated trending claims background scheduler using NewsAPI.

## [2.0.0]
### Added
- Real-time community detection feed powered by Supabase WebSockets.
- File upload support (PDF, DOCX, TXT) via Trafilatura.

## [1.0.0]
### Added
- Initial Hackathon Release by Atharv Sawane and Shashank Kalwa.
- Fake News detection using `jy46604790/Fake-News-Bert-Detect`.
- Claim validation via `whispAI/ClaimBuster-DeBERTaV2`.
- Base React frontend and FastAPI backend.
