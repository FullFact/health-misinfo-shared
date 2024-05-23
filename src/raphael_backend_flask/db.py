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


table_video_transcripts = """
    CREATE TABLE video_transcripts (
        id TEXT PRIMARY KEY,
        url TEXT,
        metadata TEXT,
        transcript TEXT,
        status TEXT
    );
    """

table_training_claims = """
    CREATE TABLE training_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT,
        claim TEXT,
        label TEXT,
        offset_ms INTEGER,
        FOREIGN KEY (video_id) REFERENCES video_transcripts(id)
    );
    """

table_inferred_claims = """
    CREATE TABLE inferred_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id TEXT,
        claim TEXT,
        label TEXT,
        model TEXT,
        offset_ms INTEGER,
        FOREIGN KEY (video_id) REFERENCES video_transcripts(id)
    );
    """


def create_database(path: str) -> None:
    db: Connection = sqlite3.connect(path)

    create_table(db, table_video_transcripts)
    create_table(db, table_training_claims)
    create_table(db, table_inferred_claims)

    db.close()


if __name__ == "__main__":
    create_database("database.db")
