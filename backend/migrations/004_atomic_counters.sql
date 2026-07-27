-- ============================================================
-- VeritasAI Phase 17 — Tier 3 Remediation
-- RPCs for Atomic Operations and Aggregations
-- ============================================================

-- 1. Atomic vote increment
CREATE OR REPLACE FUNCTION increment_vote(news_id UUID, vote_type TEXT)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  res json;
BEGIN
  IF vote_type = 'true' THEN
    UPDATE analyzed_news SET vote_true = vote_true + 1 WHERE id = news_id;
  ELSIF vote_type = 'false' THEN
    UPDATE analyzed_news SET vote_false = vote_false + 1 WHERE id = news_id;
  END IF;
  
  SELECT json_build_object('vote_true', vote_true, 'vote_false', vote_false)
  INTO res
  FROM analyzed_news WHERE id = news_id;
  
  RETURN res;
END;
$$;


-- 2. Fast Dashboard Stats Aggregation (Avoids OOM DoS)
CREATE OR REPLACE FUNCTION get_dashboard_stats()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  total_count INT;
  credible_count INT;
  false_count INT;
  mixed_count INT;
  opinion_count INT;
  insufficient_count INT;
  avg_conf INT;
BEGIN
  -- Basic counts
  SELECT count(*) INTO total_count FROM analyzed_news;
  
  -- The dashboard previously looked at `analyses` table, but now we use `analyzed_news`.
  -- Wait, the `stats.py` was reading from `analyses`. But `analyses` table is missing!
  -- We should aggregate `analyzed_news` instead.
  
  SELECT 
    COUNT(*) FILTER (WHERE overall_verdict IN ('Credible', 'Likely True', 'CREDIBLE', 'MOSTLY_TRUE')),
    COUNT(*) FILTER (WHERE overall_verdict IN ('False', 'Likely False', 'FALSE', 'MOSTLY_FALSE')),
    COUNT(*) FILTER (WHERE overall_verdict IN ('Mixed / Misleading', 'MIXED')),
    COUNT(*) FILTER (WHERE overall_verdict = 'Opinion / Not Fact-Checkable'),
    COUNT(*) FILTER (WHERE overall_verdict = 'Insufficient Evidence'),
    COALESCE(ROUND(AVG(overall_confidence)), 0)
  INTO 
    credible_count, false_count, mixed_count, opinion_count, insufficient_count, avg_conf
  FROM analyzed_news;

  RETURN json_build_object(
    'total', total_count,
    'credibleCount', credible_count,
    'falseCount', false_count,
    'mixedCount', mixed_count,
    'opinionCount', opinion_count,
    'insufficientCount', insufficient_count,
    'avgConfidence', avg_conf,
    'byCategory', '[]'::json, -- Category logic can be stubbed or expanded if a category column is added
    'confidenceBuckets', '{}'::json,
    'verdictDistribution', json_build_object(
      'Credible', credible_count,
      'False', false_count,
      'Mixed / Misleading', mixed_count,
      'Opinion / Not Fact-Checkable', opinion_count,
      'Insufficient Evidence', insufficient_count
    )
  );
END;
$$;
