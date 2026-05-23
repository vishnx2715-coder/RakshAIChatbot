-- ═══════════════════════════════════════════════════════════
-- RAKSHA — Supabase users table migration (v3 — fixed order)
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ═══════════════════════════════════════════════════════════

-- Step 1: Add ALL missing columns first
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS last_login    TIMESTAMPTZ DEFAULT now(),
  ADD COLUMN IF NOT EXISTS login_count   INTEGER     DEFAULT 0,
  ADD COLUMN IF NOT EXISTS auth_provider TEXT        DEFAULT 'email';

-- Step 2: Backfill after columns exist
UPDATE users SET last_login   = now()    WHERE last_login   IS NULL;
UPDATE users SET login_count  = 1        WHERE login_count  IS NULL OR login_count = 0;
UPDATE users SET auth_provider = 'email' WHERE auth_provider IS NULL;

-- Step 3: Verify
SELECT email, name, joined, last_login, login_count, auth_provider, lang
FROM users
ORDER BY joined DESC
LIMIT 20;
