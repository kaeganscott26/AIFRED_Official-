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
