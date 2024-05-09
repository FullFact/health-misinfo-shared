from dotenv import load_dotenv
import requests

load_dotenv()

import os
import json
from typing import Any
import sqlite3
from sqlite3 import Connection, Row
from urllib.parse import urlparse, parse_qs

from flask import Flask, redirect, request, jsonify, g, url_for
from flask.typing import ResponseReturnValue
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


from db import create_database
from vertex import process_video
from youtube import download_captions, extract_title

DB_PATH = os.getenv("DB_PATH", "database.db")

app = Flask(__name__)
CORS(app)

auth = HTTPBasicAuth()

users = {
    user: generate_password_hash(password)
    for user, password in (item.split(":") for item in os.environ["USERS"].split(","))
}


@auth.verify_password
def verify_password(username: str, password: str) -> str | None:
    if username in users and check_password_hash(users[username], password):
        return username


def get_db_connection() -> Connection:
    conn = g.get("_database")
    if not conn:
        if not os.path.isfile(DB_PATH):
            create_database(DB_PATH)
        conn = g._database = sqlite3.connect(f"file:{DB_PATH}?mode=rw", uri=True)
    conn.row_factory = Row
    return conn


@app.teardown_appcontext
def teardown_db_connection(_: Any) -> None:
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


@app.get("/api/transcripts/")
@auth.login_required
def get_transcripts() -> ResponseReturnValue:
    transcripts = execute_sql("SELECT * FROM video_transcripts")
    return jsonify([{**t} for t in transcripts]), 200


def extract_youtube_id(url: str) -> str:
    try:
        parsed = urlparse(url)
        if parsed.netloc == "youtu.be":
            return parsed.path[1:]

        if parsed.netloc == "" and len(parsed.path) == 11:
            # if it's 11 chars like a video id, wing it
            return parsed.path

        queries = parse_qs(parsed.query)
        # assume this exists
        return queries["v"][0]
    except:
        raise Exception


def update_video_transcript(
    video_id: str,
    url: str,
    metadata: dict | None,
    transcript: list[dict] | None,
    status: str,
) -> None:
    execute_sql(
        "REPLACE INTO video_transcripts (id, url, metadata, transcript, status) VALUES (?, ?, ?, ?, ?)",
        (
            video_id,
            url,
            json.dumps(metadata),
            # siiigh
            "\n".join(sentence["sentence_text"] for sentence in transcript)
            if transcript
            else None,
            status,
        ),
    )


@app.post("/api/transcripts/")
@auth.login_required
def post_transcripts() -> ResponseReturnValue:
    data = request.get_json()
    video_id = extract_youtube_id(data["id"])
    video_url = f"https://youtube.com/watch?v={video_id}"
    with requests.get(video_url, timeout=60) as resp:
        video_html = resp.text

    # Make transcript processing
    update_video_transcript(video_id, video_url, None, None, "processing")

    title = extract_title(video_html)
    metadata = {"title": title}
    transcript = download_captions(video_html)

    # Add transcript text
    update_video_transcript(video_id, video_url, metadata, transcript, "processing")
    claims = process_video(video_id, transcript)

    for claim in claims:
        execute_sql(
            "INSERT INTO inferred_claims (video_id, claim, label, model, offset_ms) VALUES (?, ?, ?, ?, ?)",
            (
                video_id,
                claim["claim"],
                "health",
                "gemini-pro",
                claim["offset_ms"],
            ),
        )

    # Mark transcript done
    update_video_transcript(video_id, video_url, metadata, transcript, "completed")

    return jsonify(id=data["id"]), 201


@app.get("/api/transcripts/<string:id>")
@auth.login_required
def get_transcript(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    transcripts = execute_sql(
        "SELECT * FROM video_transcripts WHERE id = ?", (video_id,)
    )
    if transcripts:
        return jsonify(**transcripts[0]), 200
    return jsonify({"error": "transcript not found"}), 404


@app.get("/api/transcripts/<string:id>/status")
@auth.login_required
def get_transcript_status(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    transcripts = execute_sql(
        "SELECT * FROM video_transcripts WHERE id = ?", (video_id,)
    )
    if transcripts:
        return jsonify({"status": transcripts[0]["status"]}), 200
    return jsonify({"error": "transcript not found"}), 404


@app.delete("/api/transcripts/<string:id>")
@auth.login_required
def delete_transcript(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    execute_sql("DELETE FROM video_transcripts WHERE id = ?", (video_id,))
    return "", 204


@app.post("/api/training_claims")
@auth.login_required
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


@app.get("/api/training_claims/<string:id>")
@auth.login_required
def get_training_claims(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    claims = execute_sql("SELECT * FROM training_claims WHERE video_id = ?", (video_id,))
    return jsonify([{**c} for c in claims]), 200


@app.get("/api/training_claims/<string:id>/status")
@auth.login_required
def get_training_claims_status(id: str) -> ResponseReturnValue:
    return redirect(url_for("get_transcript_status", id=id))


@app.delete("/api/training_claims/<string:id>")
@auth.login_required
def delete_training_claim(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    execute_sql("DELETE FROM training_claims WHERE id = ?", (video_id,))
    return "", 204


@app.post("/api/inferred_claims")
@auth.login_required
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


@app.get("/api/inferred_claims/<string:id>")
@auth.login_required
def get_inferred_claims(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    claims = execute_sql("SELECT * FROM inferred_claims WHERE video_id = ?", (video_id,))
    return jsonify([{**c} for c in claims]), 200


@app.get("/api/inferred_claims/<string:id>/status")
@auth.login_required
def get_inferred_claims_status(id: str) -> ResponseReturnValue:
    return redirect(url_for("get_transcript_status", id=id))


@app.delete("/api/inferred_claims/<string:id>")
@auth.login_required
def delete_inferred_claim(id: str) -> ResponseReturnValue:
    video_id = extract_youtube_id(id)
    execute_sql("DELETE FROM inferred_claims WHERE id = ?", (video_id,))
    return "", 204


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
