PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS releases (
  channel TEXT PRIMARY KEY CHECK (channel IN ('beta', 'flagship')),
  version TEXT NOT NULL,
  tag TEXT NOT NULL,
  url TEXT NOT NULL,
  published_at TEXT,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  updated_at TEXT NOT NULL
);

INSERT INTO releases (channel, version, tag, url, published_at, metadata_json, updated_at)
VALUES
  ('beta', '0.3.6', 'v0.3.6-beta-stable', 'https://github.com/kaeganscott26/AIFRED/releases/tag/v0.3.6-beta-stable', '2026-09-07T01:30:42Z', '{"r2_prefix":"v0.3.6-installer-ai-alias","status":"published"}', '2026-09-08T00:00:00Z'),
  ('flagship', '4.0.0-alpha.2', 'v4.0.0-alpha.2', 'https://north3rnlight3r.com', '2026-09-08T00:00:00Z', '{"status":"development","artifact_published":false}', '2026-09-08T00:00:00Z')
ON CONFLICT(channel) DO NOTHING;

CREATE TABLE IF NOT EXISTS inquiries (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  message TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new'
);
CREATE INDEX IF NOT EXISTS inquiries_created_at ON inquiries(created_at DESC);

CREATE TABLE IF NOT EXISTS activity (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  event_type TEXT NOT NULL,
  request_id TEXT,
  product TEXT,
  channel TEXT,
  version TEXT,
  platform TEXT,
  route TEXT,
  method TEXT,
  status INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS activity_created_at ON activity(created_at DESC);
CREATE INDEX IF NOT EXISTS activity_event_type ON activity(event_type, created_at DESC);

CREATE TABLE IF NOT EXISTS analytics_rollups (
  day TEXT NOT NULL,
  event_type TEXT NOT NULL,
  product TEXT NOT NULL DEFAULT '',
  channel TEXT NOT NULL DEFAULT '',
  platform TEXT NOT NULL DEFAULT '',
  count INTEGER NOT NULL DEFAULT 0,
  last_seen TEXT NOT NULL,
  PRIMARY KEY (day, event_type, product, channel, platform)
);

CREATE TABLE IF NOT EXISTS admin_sessions (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL,
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS admin_sessions_expires_at ON admin_sessions(expires_at);

CREATE TABLE IF NOT EXISTS idempotency_keys (
  key TEXT PRIMARY KEY,
  route TEXT NOT NULL,
  client_key TEXT NOT NULL,
  state TEXT NOT NULL CHECK (state IN ('pending', 'complete')),
  created_at TEXT NOT NULL,
  expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idempotency_keys_expires_at ON idempotency_keys(expires_at);

CREATE TABLE IF NOT EXISTS request_rollups (
  minute TEXT NOT NULL,
  route TEXT NOT NULL,
  client_key TEXT NOT NULL DEFAULT '',
  product TEXT NOT NULL DEFAULT '',
  channel TEXT NOT NULL DEFAULT '',
  purpose TEXT NOT NULL DEFAULT '',
  status INTEGER NOT NULL,
  rate_limit_outcome TEXT NOT NULL DEFAULT '',
  cache_status TEXT NOT NULL DEFAULT '',
  provider_calls INTEGER NOT NULL DEFAULT 0,
  d1_writes INTEGER NOT NULL DEFAULT 0,
  queue_events INTEGER NOT NULL DEFAULT 0,
  r2_downloads INTEGER NOT NULL DEFAULT 0,
  requests INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (
    minute, route, client_key, product, channel, purpose, status,
    rate_limit_outcome, cache_status
  )
);
CREATE INDEX IF NOT EXISTS request_rollups_minute ON request_rollups(minute DESC);
