-- ============================================================
-- VeritasAI Phase 8 — Live Feed & Trending Claims Tables
-- Run once in Supabase SQL editor.
-- After running, enable Realtime on analyzed_news:
--   ALTER PUBLICATION supabase_realtime ADD TABLE analyzed_news;
-- ============================================================

-- Table: analyzed_news
-- One row per analyzed article/headline. Both user submissions
-- and cron-triggered analyses land here.
CREATE TABLE IF NOT EXISTS analyzed_news (
  id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  headline            TEXT        NOT NULL,
  headline_hash       TEXT        NOT NULL,
  summary             TEXT,
  source_url          TEXT,
  analysis_source     TEXT        NOT NULL DEFAULT 'user_submitted',
  overall_verdict     TEXT        NOT NULL,
  overall_confidence  FLOAT,
  content_type        TEXT        NOT NULL DEFAULT 'news_report',
  claim_count         INT         NOT NULL DEFAULT 0,
  claims              JSONB,
  explainability      JSONB,
  top_sources         JSONB,
  reasoning_summary   TEXT,
  reanalysis_count    INT         NOT NULL DEFAULT 0,
  last_analyzed_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  view_count          INT         NOT NULL DEFAULT 1,
  vote_true           INT         NOT NULL DEFAULT 0,
  vote_false          INT         NOT NULL DEFAULT 0,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_analyzed_news_headline_hash
  ON analyzed_news (headline_hash);
CREATE INDEX IF NOT EXISTS idx_analyzed_news_created_at
  ON analyzed_news (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analyzed_news_verdict
  ON analyzed_news (overall_verdict);


-- Table: trending_claims
-- One row per unique factual claim, aggregated across all articles.
CREATE TABLE IF NOT EXISTS trending_claims (
  id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  claim_text       TEXT        NOT NULL UNIQUE,
  claim_hash       TEXT        NOT NULL UNIQUE,
  current_verdict  TEXT        NOT NULL,
  current_confidence FLOAT,
  check_count      INT         NOT NULL DEFAULT 1,
  supporting_sources JSONB,
  verdict_history  JSONB,
  first_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_checked_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  news_ids         JSONB       DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_trending_claims_check_count
  ON trending_claims (check_count DESC);
CREATE INDEX IF NOT EXISTS idx_trending_claims_last_checked
  ON trending_claims (last_checked_at DESC);


-- Enable Realtime on analyzed_news for live feed updates
ALTER PUBLICATION supabase_realtime ADD TABLE analyzed_news;
