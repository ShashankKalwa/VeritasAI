-- VeritasAI v2 Migration — run once in Supabase SQL editor
-- This script adds new columns for the v2 claim-level verification system
-- and remaps existing verdict labels to the new taxonomy.

-- Step 1: Add new columns if they don't exist
ALTER TABLE analyses
  ADD COLUMN IF NOT EXISTS overall_verdict    TEXT    DEFAULT 'Insufficient Evidence',
  ADD COLUMN IF NOT EXISTS overall_confidence FLOAT   DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS content_type       TEXT    DEFAULT 'news_report',
  ADD COLUMN IF NOT EXISTS claim_count        INT     DEFAULT 0,
  ADD COLUMN IF NOT EXISTS claims             JSONB   DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS explainability     JSONB   DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS top_sources        JSONB   DEFAULT NULL;

-- Step 2: Remap old binary/5-label verdicts on existing rows
UPDATE analyses SET overall_verdict = 'Credible'          WHERE verdict = 'REAL' OR verdict = 'Credible' OR verdict = 'CREDIBLE';
UPDATE analyses SET overall_verdict = 'False'             WHERE verdict = 'FAKE' OR verdict = 'FALSE';
UPDATE analyses SET overall_verdict = 'Likely True'       WHERE verdict = 'MOSTLY_TRUE' OR verdict = 'Mostly True';
UPDATE analyses SET overall_verdict = 'Mixed / Misleading' WHERE verdict = 'MIXED' OR verdict = 'Mixed / Misleading';
UPDATE analyses SET overall_verdict = 'Likely False'      WHERE verdict = 'MOSTLY_FALSE' OR verdict = 'Mostly False';

-- Step 3: Verify migration
SELECT overall_verdict, COUNT(*) FROM analyses GROUP BY overall_verdict ORDER BY overall_verdict;
