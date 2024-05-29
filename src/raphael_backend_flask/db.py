import os
import sqlite3
from sqlite3 import Connection, Row
from typing import Any

from flask import g

Table = tuple[str, dict, list[str]]
"""
Not overdoing this
"""


DB_PATH = os.getenv("DB_PATH", "database.db")


def create_table(db: Connection, statement: str) -> None:
    cur = db.cursor()
    cur.execute(statement)
    db.commit()


def get_db_connection() -> Connection:
    conn = g.get("_database")
    if not conn:
        if not os.path.isfile(DB_PATH):
            create_database(DB_PATH)
        conn = g._database = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True)
    conn.row_factory = Row
    return conn


def execute_sql(sql: str, params: tuple[Any, ...] = ()) -> list[Row]:
    """Open/close the database for each request, we don't expect to make many."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON")
    cur.execute(sql, params)
    data = cur.fetchall()
    conn.commit()
    cur.close()
    return data


def create_claim_extraction_run(
    youtube_id: str,
    metadata: str,
    transcript: str,
) -> int:
    execute_sql(
        "REPLACE INTO youtube_videos (id, metadata, transcript) VALUES (?, ?, ?)",
        (
            youtube_id,
            metadata,
            transcript,
        ),
    )
    result = execute_sql(
        "INSERT INTO claim_extraction_runs (youtube_id, model, status) VALUES (?, ?, ?) RETURNING id",
        (
            youtube_id,
            "gemini-pro",
            "processing",
        ),
    )
    return result[0]["id"]


def update_claim_extraction_run(
    video_id: str,
    **kwargs: str,
) -> None:
    update_cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])

    execute_sql(
        f"UPDATE claim_extraction_runs SET {update_cols} WHERE ID = ?",
        (
            *kwargs.values(),
            video_id,
        ),
    )


# Note that metadata and transcript contain JSON data
table_youtube_videos = """
    CREATE TABLE youtube_videos (
        id TEXT PRIMARY KEY,
        metadata TEXT,
        transcript TEXT
    );
    """

table_claim_extraction_runs = """
    CREATE TABLE claim_extraction_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT,
        model TEXT,
        status TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (youtube_id) REFERENCES youtube_videos (id)
    );
    """

# Note that label contains JSON data
table_inferred_claims = """
    CREATE TABLE inferred_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        claim TEXT,
        raw_sentence_text TEXT,
        label TEXT,
        offset_start_s REAL,
        offset_end_s REAL,
        FOREIGN KEY (run_id) REFERENCES claim_extraction_runs (id)
    );
    """

# Note that label contains JSON data
table_training_claims = """
    CREATE TABLE training_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT,
        claim TEXT,
        label TEXT
    );
    """


def create_database(path: str) -> None:
    db: Connection = sqlite3.connect(path)

    create_table(db, table_youtube_videos)
    create_table(db, table_claim_extraction_runs)
    create_table(db, table_training_claims)
    create_table(db, table_inferred_claims)

    db.close()


if __name__ == "__main__":
    create_database("database.db")
