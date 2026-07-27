-- ============================================================
-- VeritasAI Phase 17 — Tier 1 Security Remediation
-- Enable Row-Level Security (RLS) on all public tables
-- ============================================================

-- 1. Enable RLS on all tables
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE analyzed_news ENABLE ROW LEVEL SECURITY;
ALTER TABLE trending_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE dataset ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing public policies if they exist (idempotent)
DROP POLICY IF EXISTS "Enable read access for all users" ON analyses;
DROP POLICY IF EXISTS "Enable read access for all users" ON analyzed_news;
DROP POLICY IF EXISTS "Enable read access for all users" ON trending_claims;
DROP POLICY IF EXISTS "Enable read access for all users" ON dataset;

-- 3. Create SELECT policies for anon and authenticated users
-- The application only reads these from the frontend directly.
-- All writes happen via the FastAPI backend using the service_role key, 
-- which bypasses RLS automatically.

CREATE POLICY "Enable read access for all users" 
ON analyses FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" 
ON analyzed_news FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" 
ON trending_claims FOR SELECT USING (true);

CREATE POLICY "Enable read access for all users" 
ON dataset FOR SELECT USING (true);

-- No INSERT, UPDATE, or DELETE policies are created for anon/authenticated roles.
-- This strictly locks down the DB against arbitrary frontend writes (FINDING-05-1).
