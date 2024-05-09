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
