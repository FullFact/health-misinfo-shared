import sqlite3
from sqlite3 import Connection

Table = tuple[str, dict, list[str]]
"""
Not overdoing this
"""


def create_table(db: Connection, statement: str) -> None:
    cur = db.cursor()
    cur.execute(statement)
    db.commit()


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
        timestamp INTEGER,
        FOREIGN KEY (youtube_id) REFERENCES youtube_videos (id)
    );
    """

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

table_training_claims = """
    CREATE TABLE training_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        youtube_id TEXT,
        claim TEXT,
        label TEXT,
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
