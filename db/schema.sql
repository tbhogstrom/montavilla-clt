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

CREATE TABLE IF NOT EXISTS posts (
  id           TEXT PRIMARY KEY,
  type         TEXT NOT NULL DEFAULT 'discussion' CHECK (type IN ('discussion', 'update')),
  title        TEXT NOT NULL,
  body         TEXT,
  image_url    TEXT,
  display_name TEXT NOT NULL,
  neighborhood TEXT,
  likes        INTEGER NOT NULL DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT NOW(),
  is_deleted   BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS posts_created_at_idx ON posts (created_at DESC);
CREATE INDEX IF NOT EXISTS posts_type_idx ON posts (type);
