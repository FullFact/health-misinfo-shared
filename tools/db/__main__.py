import sqlite3
from sqlite3 import Connection

Table = tuple[str, dict, list[str]]
"""
Not overdoing this
"""

def create_table(db: Connection, name: str, columns: dict, extras: list[str]) -> None:
    cur = db.cursor()

    sql = f"CREATE TABLE {name} ("
    sql += ", ".join(f"{column} {type}" for column, type in columns.items())
    sql += ", ".join(["", *extras])  # head "" adds ", " if extras is not empty
    sql += ")"

    cur.execute(sql)
    db.commit()


table_video_transcripts: Table = ("transcripts", {
    "id": "TEXT PRIMARY KEY",
    "url": "TEXT",
    "metadata": "TEXT",
    "transcript": "TEXT",
}, [])


table_training_claims: Table = ("training_claims", {
    "id": "TEXT",
    "claim": "TEXT",
    "label": "TEXT",
    "offset_ms": "INTEGER",
}, ["FOREIGN KEY (id) REFERENCES transcripts (id)"])


table_inferred_claims: Table = ("inferred_claims", {
    "id": "TEXT",
    "claim": "TEXT",
    "label": "TEXT",
    "model": "TEXT",
    "offset_ms": "INTEGER",
}, ["FOREIGN KEY (id) REFERENCES transcripts (id)"])


if __name__ == "__main__":
    db: Connection = sqlite3.connect("database.db")

    create_table(db, *table_video_transcripts)
    create_table(db, *table_training_claims)
    create_table(db, *table_inferred_claims)

    db.close()
