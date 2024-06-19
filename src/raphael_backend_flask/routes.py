from datetime import datetime
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

from raphael_backend_flask.auth import auth, get_user_sql, create_user_sql, update_user_password_sql, disable_user_sql
from raphael_backend_flask.db import execute_sql
from raphael_backend_flask.llm import extract_claims
from raphael_backend_flask.process import download_transcript
from raphael_backend_flask.youtube import extract_youtube_id

routes = Blueprint("routes", __name__)


@routes.get("/")
@auth.login_required
def get_home() -> ResponseReturnValue:
    runs = execute_sql(
        """
        SELECT *
        FROM claim_extraction_runs, youtube_videos
        WHERE youtube_id = youtube_videos.id
        ORDER BY timestamp DESC
        LIMIT 20
    """
    )
    return render_template(
        "home.html",
        runs=[{**t, **{"metadata": json.loads(t["metadata"])}} for t in runs],
    )


@routes.post("/post")
@auth.login_required
def post_youtube_url() -> ResponseReturnValue:
    user = auth.current_user()
    query = request.form["q"]
    try:
        youtube_id = extract_youtube_id(query)
    except Exception:
        flash("That YouTube URL didn’t work", "danger")
        return redirect(url_for("routes.get_home"))

    try:
        run_id = download_transcript(user.user_id, youtube_id)
    except Exception as e:
        flash(f"Something went wrong: {e}", "danger")
        return redirect(url_for("routes.get_home"))

    return redirect(url_for("routes.get_video_analysis", run_id=run_id))


@routes.get("/runs/<run_id>")
@auth.login_required
def get_video_analysis(run_id: int) -> ResponseReturnValue:
    runs = execute_sql(
        """
        SELECT *
        FROM claim_extraction_runs, youtube_videos
        WHERE youtube_id = youtube_videos.id
        AND claim_extraction_runs.id = ?
    """,
        (run_id,),
    )
    if not runs:
        flash("Transcript not found", "danger")
        return redirect(url_for("routes.get_home"))

    run = dict(runs[0])
    run["metadata"] = json.loads(run["metadata"])
    run["transcript"] = json.loads(run["transcript"])

    claims_sql = execute_sql(
        "SELECT * FROM inferred_claims WHERE run_id = ?", (run_id,)
    )
    claims = [
        {**claim, **{"labels": json.loads(claim["labels"])}}
        for claim in claims_sql
    ]

    if run["status"] == "processing":
        if claims:
            run["status"] = "incomplete"
        else:
            claims = extract_claims(dict(run))

    return stream_template(
        "video_analysis.html",
        claims=claims,
        started=datetime.now(),
        **run,
    )


@routes.delete("/api/runs/<int:run_id>")
@auth.login_required
def delete_run(run_id: int) -> ResponseReturnValue:
    execute_sql("DELETE FROM claim_extraction_runs WHERE id = ?", (run_id,))
    return "", 204


@routes.post("/api/training_claims")
@auth.login_required
def create_training_claim() -> ResponseReturnValue:
    data = request.get_json()
    execute_sql(
        "INSERT INTO training_claims (youtube_id, claim, labels) VALUES (?, ?, ?)",
        (
            data["youtube_id"],
            data["claim"],
            data["labels"],
        ),
    )
    return jsonify(data), 201


@routes.get("/api/training_claims/<string:youtube_id>")
@auth.login_required
def get_training_claims(youtube_id: str) -> ResponseReturnValue:
    claims = execute_sql(
        "SELECT * FROM training_claims WHERE youtube_id = ?", (youtube_id,)
    )
    return jsonify([{**c} for c in claims]), 200


@routes.delete("/api/training_claims/<int:id>")
@auth.login_required
def delete_training_claim(id: int) -> ResponseReturnValue:
    execute_sql("DELETE FROM training_claims WHERE id = ?", (id,))
    return "", 204


@routes.post("/api/register")
@auth.login_required(role="admin")
def post_register_user() -> ResponseReturnValue:
    username: str = request.form["username"]
    password: str = request.form["password"]
    admin: bool = True if request.form.get("administrator") else False
    create_user_sql(username, password, admin)
    return username, 200

@routes.patch("/api/users/<string:username>")
@auth.login_required(role="admin")
def patch_user(username: str) -> ResponseReturnValue:
    """Used to update a user's password."""
    password = request.form["password"]
    update_user_password_sql(username, password)
    return "", 200

@routes.delete("/api/users/<string:username>")
@auth.login_required(role="admin")
def disable_user(username: str) -> ResponseReturnValue:
    disable_user_sql(username)
    return "", 200
