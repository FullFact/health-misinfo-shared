import os
import sqlite3
from sqlite3 import Connection, Row
from typing import Any

from flask import g
from werkzeug.security import generate_password_hash

Table = tuple[str, dict, list[str]]
"""
Not overdoing this
"""


DB_PATH = os.getenv("DB_PATH", "database.db")

def execute_statement_unsafe(db: Connection, statement: str) -> None:
    cur = db.cursor()
    cur.execute(statement)
    db.commit()

def create_table(db: Connection, statement: str) -> None:
    execute_statement_unsafe(db, statement)

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
    CREATE TABLE IF NOT EXISTS youtube_videos (
        id TEXT PRIMARY KEY,
        metadata TEXT,
        transcript TEXT
    );
    """

table_claim_extraction_runs = """
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
    """

# Note that labels contains JSON data
table_inferred_claims = """
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
    """

# Note that labels contains JSON data
table_training_claims = """
    CREATE TABLE IF NOT EXISTS training_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT,
        claim TEXT,
        labels TEXT
    );
    """

# Note that BOOL in sqlite is just INTEGER
table_users = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        admin BOOL NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
"""


def create_database(path: str) -> None:
    db: Connection = sqlite3.connect(path)

    create_table(db, table_youtube_videos)
    create_table(db, table_claim_extraction_runs)
    create_table(db, table_training_claims)
    create_table(db, table_inferred_claims)
    create_table(db, table_users)

    default_username = "fullfact"
    default_password = generate_password_hash("changeme")
    try:
        execute_statement_unsafe(db, f"""
            INSERT INTO users (username, password_hash, admin) VALUES (
                '{default_username}',
                '{default_password}',
                TRUE
            )  
        """)
    except sqlite3.IntegrityError:
        pass

    db.close()

