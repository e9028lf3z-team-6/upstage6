-- Add Document.meta_json
ALTER TABLE documents ADD COLUMN meta_json TEXT DEFAULT '{}';

-- Add Analysis columns
ALTER TABLE analyses ADD COLUMN decision TEXT;
ALTER TABLE analyses ADD COLUMN has_issues BOOLEAN;
ALTER TABLE analyses ADD COLUMN issue_counts_json TEXT DEFAULT '{}';
CREATE TABLE IF NOT EXISTS eval_runs (
  id TEXT PRIMARY KEY,
  document_id TEXT,
  metrics_json TEXT NOT NULL,
  scores_json TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
