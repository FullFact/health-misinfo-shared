import json
import traceback
from datetime import datetime

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

from raphael_backend_flask.auth import (
    auth,
    create_user_sql,
    disable_user_sql,
    update_user_password_sql,
)
from raphael_backend_flask.db import execute_sql
from raphael_backend_flask.exceptions import FlashException
from raphael_backend_flask.llm import (
    extract_multimodal_claims,
    extract_transcript_claims,
)
from raphael_backend_flask.multimodal import (
    handle_multimodal_url,
    valid_multimodal_video_url,
)
from raphael_backend_flask.youtube import (
    handle_youtube_query,
    valid_youtube_video_query,
)

routes = Blueprint("routes", __name__)


@routes.get("/")
@auth.login_required
def get_home() -> ResponseReturnValue:
    user = auth.current_user()
    if user is None:
        return "", 401

    runs = execute_sql(
        """
            SELECT
                r.*,
                y.id as youtube_id,
                r.multimodal_video_id as multimodal_video_id,
                coalesce(y.metadata, m.metadata) as metadata
            FROM claim_extraction_runs r
            LEFT OUTER JOIN youtube_videos y ON r.youtube_id = y.id
            LEFT OUTER JOIN multimodal_videos m ON r.multimodal_video_id = m.id
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 20
        """,
        (user.user_id,),
    )
    return render_template(
        "home.html",
        runs=[{**t, **{"metadata": json.loads(t["metadata"])}} for t in runs],
    )


@routes.post("/run")
@auth.login_required
def post_video_url() -> ResponseReturnValue:
    user = auth.current_user()
    query = request.form["q"]
    if user is None:
        return "", 401
    user_id = user.user_id

    if valid_youtube_video_query(query):
        run_id = handle_youtube_query(user_id, query)
    elif valid_multimodal_video_url(query):
        run_id = handle_multimodal_url(user_id, query)
    else:
        raise FlashException("Could not process video")

    return redirect(url_for("routes.get_video_analysis", run_id=run_id))


@routes.get("/runs/<run_id>")
@auth.login_required
def get_video_analysis(run_id: int) -> ResponseReturnValue:
    runs = execute_sql(
        """
            SELECT
                r.*,
                y.id as youtube_id,
                r.multimodal_video_id as multimodal_video_id,
                coalesce(y.metadata, m.metadata) as metadata,
                coalesce(y.transcript, '[]') as transcript,
                m.video_path as video_path
            FROM claim_extraction_runs r
            LEFT OUTER JOIN youtube_videos y ON r.youtube_id = y.id
            LEFT OUTER JOIN multimodal_videos m ON r.multimodal_video_id = m.id
            WHERE r.id = ?
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
        {**claim, **{"labels": json.loads(claim["labels"])}} for claim in claims_sql
    ]

    mode = "transcript" if run["youtube_id"] else "multimodal"

    if run["status"] == "processing":
        if claims:
            run["status"] = "incomplete"
        elif mode == "transcript":
            claims = extract_transcript_claims(dict(run))
        elif mode == "multimodal":
            claims = extract_multimodal_claims(dict(run))

    return stream_template(
        mode + "_analysis.html",
        claims=claims,
        started=datetime.now(),
        mode=mode,
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


@routes.errorhandler(Exception)
def handle_exception(e) -> ResponseReturnValue:
    if request.path.startswith("/api/"):
        # if it looks like an API endpoint, return JSON
        return jsonify(message=str(e)), 500

    if isinstance(e, FlashException):
        flash(e.message, e.category)
    else:
        flash("An unexpected error occurred.", category="danger")
        print(traceback.format_exc())
        print(e)
    return redirect(url_for("routes.get_home"))
