import json

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    stream_template,
    url_for,
)
from flask.typing import ResponseReturnValue

from raphael_backend_flask.auth import auth
from raphael_backend_flask.db import execute_sql
from raphael_backend_flask.process import download_transcript, extract_claims
from raphael_backend_flask.youtube import extract_youtube_id

routes = Blueprint("routes", __name__)


@routes.get("/")
@auth.login_required
def get_home() -> ResponseReturnValue:
    runs = execute_sql("""
        SELECT *
        FROM claim_extraction_runs, youtube_videos
        WHERE youtube_id = youtube_videos.id
        ORDER BY timestamp DESC
    """)
    return render_template(
        "home.html",
        runs=[
            {**t, **{"metadata": json.loads(t["metadata"])}} for t in runs
        ],
    )


@routes.post("/post")
def post_youtube_url() -> ResponseReturnValue:
    query = request.form["q"]
    try:
        youtube_id = extract_youtube_id(query)
    except Exception:
        flash("That YouTube URL didn’t work", "danger")
        return redirect(url_for("routes.get_home"))

    try:
        run_id = download_transcript(youtube_id)
    except Exception as e:
        flash(f"Something went wrong: {e}", "danger")
        return redirect(url_for("routes.get_home"))

    return redirect(url_for("routes.get_video_analysis", run_id=run_id))


@routes.get("/runs/<run_id>")
@auth.login_required
def get_video_analysis(run_id: int) -> ResponseReturnValue:
    runs = execute_sql("""
        SELECT *
        FROM claim_extraction_runs, youtube_videos
        WHERE youtube_id = youtube_videos.id
        AND claim_extraction_runs.id = ?
    """, (run_id,))
    if not runs:
        flash("Transcript not found", "danger")
        return redirect(url_for("routes.get_home"))

    run = runs[0]

    claims_sql = execute_sql(
        "SELECT * FROM inferred_claims WHERE run_id = ?", (run_id,)
    )
    claims = [dict(claim) for claim in claims_sql]

    if not claims and run["status"] == "processing":
        claims = extract_claims(dict(run))

    return stream_template(
        "video_analysis.html",
        claims=claims,
        **{
            **run,
            **{"metadata": json.loads(run["metadata"])},
        },
    )


@routes.delete("/api/transcripts/<string:video_id>")
@auth.login_required
def delete_transcript(video_id: str) -> ResponseReturnValue:
    execute_sql("DELETE FROM video_transcripts WHERE id = ?", (video_id,))
    return "", 204


@routes.post("/api/training_claims")
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


@routes.get("/api/training_claims/<string:video_id>")
@auth.login_required
def get_training_claims(video_id: str) -> ResponseReturnValue:
    claims = execute_sql(
        "SELECT * FROM training_claims WHERE video_id = ?", (video_id,)
    )
    return jsonify([{**c} for c in claims]), 200


@routes.delete("/api/training_claims/<string:id>")
@auth.login_required
def delete_training_claim(id: str) -> ResponseReturnValue:
    execute_sql("DELETE FROM training_claims WHERE id = ?", (id,))
    return "", 204
