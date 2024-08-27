import os
import sqlite3
from sqlite3 import Connection, Row
from typing import Any
from pathlib import Path

from flask import g
from werkzeug.security import generate_password_hash


DB_PATH = os.getenv("DB_PATH", "database.db")
MIGRATION_VERSION = 2


def run_migrations() -> None:
    conn = sqlite3.connect(f"{DB_PATH}")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER NOT NULL UNIQUE DEFAULT 0,
            performed DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    ).close()

    cur = conn.execute("SELECT max(version) from migrations")
    current_version = cur.fetchone()[0] or 0
    cur.close()

    current_dir = os.path.dirname(os.path.realpath(__file__))
    print(f"Migration Current: {current_version} Target: {MIGRATION_VERSION}")
    if current_version < MIGRATION_VERSION:
        print(f"Upgrading to version {MIGRATION_VERSION}...")
        for i in range(current_version + 1, MIGRATION_VERSION + 1):
            print(f"Running migration {i}...")
            script = Path(os.path.join(current_dir, f"migrations/{i}.sql")).read_text()
            conn.executescript(script).close()
            conn.execute("INSERT INTO migrations (version) VALUES (?);", (i,)).close()

    if current_version == 0:
        create_init_user(conn)

    conn.commit()
    conn.close()


def get_db_connection() -> Connection:
    conn = g.get("_database")
    if not conn:
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
    user_id: int,
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
        "INSERT INTO claim_extraction_runs (user_id, youtube_id, model, status) VALUES (?, ?, ?, ?) RETURNING id",
        (
            user_id,
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


def create_init_user(conn: Connection) -> None:
    default_username: str = "fullfact"
    default_password: str = generate_password_hash("changeme")
    conn.execute(
        """
        INSERT INTO users (username, password_hash, admin)
        VALUES (?, ?, TRUE)
        ON CONFLICT (username) DO NOTHING
        """,
        (
            default_username,
            default_password,
        ),
    ).close()
    conn.commit()
