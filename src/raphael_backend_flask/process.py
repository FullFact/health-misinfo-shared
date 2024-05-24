import json
from typing import Generator

import requests

from health_misinfo_shared.vertex import process_video
from raphael_backend_flask.db import execute_sql
from raphael_backend_flask.youtube import download_captions, extract_title


def update_video_transcript(
    video_id: str,
    **kwargs: str,
) -> None:
    fields = ", ".join(kwargs.keys())
    entries = ", ?" * len(kwargs)

    execute_sql(
        f"REPLACE INTO video_transcripts (id, {fields}) VALUES (?{entries})",
        (
            video_id,
            *kwargs.values(),
        ),
    )


def download_transcript(video_id: str) -> None:
    video_url = f"https://youtube.com/watch?v={video_id}"
    with requests.get(video_url, timeout=60) as resp:
        video_html = resp.text

    title = extract_title(video_html)
    metadata = {"title": title}
    transcript = download_captions(video_html)

    # Add transcript text
    update_video_transcript(
        video_id,
        url=video_url,
        metadata=json.dumps(metadata),
        transcript=json.dumps(transcript),
        status="processing",
    )


def extract_claims(video_id: str, transcript: dict) -> Generator:
    sentences = json.loads(transcript["transcript"])
    claims = process_video(video_id, sentences)

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
        yield claim

    # Mark transcript done
    update_video_transcript(video_id, status="completed")
