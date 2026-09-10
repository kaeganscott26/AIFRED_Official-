CREATE TABLE IF NOT EXISTS rate_limits (
  scope TEXT NOT NULL,
  client_key TEXT NOT NULL,
  window_start INTEGER NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (scope, client_key, window_start)
);
CREATE INDEX IF NOT EXISTS rate_limits_window_start ON rate_limits(window_start);
