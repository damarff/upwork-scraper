-- =============================================
-- Supabase SQL: Create 'jobs' table
-- Jalankan ini di Supabase Dashboard → SQL Editor
-- =============================================

-- 1. Create the table
CREATE TABLE IF NOT EXISTS public.jobs (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  url TEXT,
  budget TEXT,
  description TEXT,
  published_at TIMESTAMPTZ,
  scraped_at TIMESTAMPTZ DEFAULT NOW(),
  status TEXT DEFAULT 'new'
);

-- 2. Enable Row Level Security
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

-- 3. Create policy: allow public reads (for the portfolio frontend)
CREATE POLICY "Allow public read access"
  ON public.jobs
  FOR SELECT
  USING (true);

-- 4. Create policy: allow inserts via service role or anon key
CREATE POLICY "Allow insert from anon"
  ON public.jobs
  FOR INSERT
  WITH CHECK (true);

-- 5. Enable Realtime for the jobs table
ALTER PUBLICATION supabase_realtime ADD TABLE public.jobs;

-- 6. Create index on scraped_at for fast ordering
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON public.jobs (scraped_at DESC);
