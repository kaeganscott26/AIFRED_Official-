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
  PRIMARY KEY (minute, route, client_key, product, channel, purpose, status, rate_limit_outcome, cache_status)
);
CREATE INDEX IF NOT EXISTS request_rollups_minute ON request_rollups(minute DESC);
CREATE TABLE IF NOT EXISTS references_catalog (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  metrics_json TEXT NOT NULL,
  classification_json TEXT NOT NULL DEFAULT '{}',
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);
CREATE INDEX IF NOT EXISTS references_catalog_created_at ON references_catalog(created_at DESC);
CREATE TABLE IF NOT EXISTS rate_limits (
  scope TEXT NOT NULL,
  client_key TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (scope, client_key, window_start)
);
CREATE INDEX IF NOT EXISTS rate_limits_window_start ON rate_limits(window_start);
