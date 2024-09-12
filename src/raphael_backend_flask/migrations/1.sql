BEGIN;

CREATE TABLE IF NOT EXISTS youtube_videos (
    id TEXT PRIMARY KEY,
    metadata TEXT,
    transcript TEXT
);

CREATE TABLE IF NOT EXISTS claim_extraction_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    youtube_id TEXT,
    model TEXT,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (youtube_id) REFERENCES youtube_videos (id)
);

CREATE TABLE IF NOT EXISTS inferred_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    claim TEXT,
    raw_sentence_text TEXT,
    labels TEXT,
    offset_start_s REAL,
    offset_end_s REAL,
    FOREIGN KEY (run_id) REFERENCES claim_extraction_runs (id)
);

CREATE TABLE IF NOT EXISTS training_claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    youtube_id TEXT,
    claim TEXT,
    labels TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    admin BOOL NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

COMMIT;