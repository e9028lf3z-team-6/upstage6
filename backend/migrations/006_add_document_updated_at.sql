ALTER TABLE documents ADD COLUMN updated_at DATETIME;
UPDATE documents
SET updated_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP);
