from typing import Any, Iterable
from flask import Flask, request, jsonify, g
from flask.typing import ResponseReturnValue
import sqlite3
from sqlite3 import Connection, Row

DATABASE = "database.db"

app = Flask(__name__)


def get_db_connection() -> Connection:
    conn = g.get("_database")
    if not conn:
        conn = g._database = sqlite3.connect(DATABASE)
    conn.row_factory = Row
    return conn


@app.teardown_appcontext
def teardown_db_connection(exception: Any) -> None:
    conn: Connection | None = g.get("_database")
    if conn:
        conn.close()


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


@app.get("/transcripts")
def get_transcripts() -> ResponseReturnValue:
    transcripts = execute_sql("SELECT * FROM video_transcripts")
    return jsonify([{**t} for t in transcripts]), 200


@app.post("/transcripts")
def post_transcripts() -> ResponseReturnValue:
    data = request.get_json()
    execute_sql(
        "INSERT INTO video_transcripts (id, url, metadata, transcript) VALUES (?, ?, ?, ?)",
        (
            data["id"],
            data["url"],
            data["metadata"],
            data["transcript"],
        ),
    )
    return jsonify(id=data["id"]), 201


@app.get("/transcripts/<string:id>")
def get_transcript(id: str) -> ResponseReturnValue:
    transcripts = execute_sql("SELECT * FROM video_transcripts WHERE id = ?", (id,))
    if transcripts:
        return jsonify(**transcripts[0]), 200
    return jsonify({"error": "transcript not found"}), 404


@app.delete("/transcripts/<string:id>")
def delete_transcript(id: str) -> ResponseReturnValue:
    execute_sql("DELETE FROM video_transcripts WHERE id = ?", (id,))
    execute_sql("DELETE FROM training_claims WHERE video_id = ?", (id,))
    execute_sql("DELETE FROM inferred_claims WHERE video_id = ?", (id,))
    return "", 204


@app.post("/training_claims")
def create_training_claim() -> ResponseReturnValue:
    data = request.get_json()
    execute_sql(
        "INSERT INTO training_claims (video_id, claim, label, offset_ms) VALUES (?, ?, ?, ?)",
        (
            data["video_id"],
            data["claim"],
            data["label"],
            data["offset_ms"],
        ),
    )
    return jsonify(data), 201


@app.get("/training_claims/<string:id>")
def get_training_claims(id: str) -> ResponseReturnValue:
    claims = execute_sql("SELECT * FROM training_claims WHERE video_id = ?", (id,))
    return jsonify([{**c} for c in claims]), 200


@app.post("/inferred_claims")
def create_inferred_claim() -> ResponseReturnValue:
    data = request.get_json()
    execute_sql(
        "INSERT INTO inferred_claims (video_id, claim, label, model, offset_ms) VALUES (?, ?, ?, ?, ?)",
        (
            data["video_id"],
            data["claim"],
            data["label"],
            data["model"],
            data["offset_ms"],
        ),
    )
    return jsonify(data), 201


@app.get("/inferred_claims/<string:id>")
def get_inferred_claims(id: str) -> ResponseReturnValue:
    claims = execute_sql("SELECT * FROM inferred_claims WHERE video_id = ?", (id,))
    return jsonify([{**c} for c in claims]), 200


if __name__ == "__main__":
    app.run(debug=True)
