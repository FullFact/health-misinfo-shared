BEGIN;

CREATE TABLE IF NOT EXISTS multimodal_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata TEXT NOT NULL DEFAULT '{}',
    video_path TEXT NOT NULL
);

ALTER TABLE
    claim_extraction_runs
ADD
    multimodal_video_id INTEGER;

-- SQLite doesn't support ADD CONSTRAINT to add a reference
-- from claim_extraction_runs to multimodal_videos :(
COMMIT;