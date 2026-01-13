CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    name TEXT,
    picture TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

ALTER TABLE documents ADD COLUMN user_id TEXT REFERENCES users(id);

CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents (user_id);
