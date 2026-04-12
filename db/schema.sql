-- Run once against your Neon database to initialize the schema.
-- The API route also runs CREATE TABLE IF NOT EXISTS automatically,
-- so this is provided for reference and manual setup.

CREATE TABLE IF NOT EXISTS signups (
  id           SERIAL PRIMARY KEY,
  first_name   TEXT NOT NULL DEFAULT '',
  last_name    TEXT NOT NULL DEFAULT '',
  email        TEXT NOT NULL,
  neighborhood TEXT,
  how_can_help TEXT,
  message      TEXT,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS signups_email_idx ON signups (email);
CREATE INDEX IF NOT EXISTS signups_created_at_idx ON signups (created_at DESC);
