-- ============================================================
-- VeritasAI Phase 18 — Remove Voting System
-- Drops the vote_true and vote_false columns and the RPC
-- ============================================================

-- Drop the voting RPC
DROP FUNCTION IF EXISTS increment_vote(UUID, TEXT);

-- Drop the vote columns from analyzed_news
ALTER TABLE analyzed_news DROP COLUMN IF EXISTS vote_true;
ALTER TABLE analyzed_news DROP COLUMN IF EXISTS vote_false;
