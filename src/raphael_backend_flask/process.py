import json
from typing import Generator

import requests

from health_misinfo_shared.vertex import process_video
from raphael_backend_flask.db import execute_sql
from raphael_backend_flask.youtube import download_captions, extract_title


def create_video_transcript(
    video_id: str,
    url: str,
    metadata: dict,
    transcript: list[dict],
    status: str,
) -> None:
    execute_sql(
        "REPLACE INTO video_transcripts (id, url, metadata, transcript, status) VALUES (?, ?, ?, ?, ?)",
        (
            video_id,
            url,
            metadata,
            transcript,
            status,
        ),
    )


def update_video_transcript(
    video_id: str,
    **kwargs: str,
) -> None:
    update_cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])

    execute_sql(
        f"UPDATE video_transcripts SET {update_cols} WHERE ID = ?",
        (
            *kwargs.values(),
            video_id,
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
    create_video_transcript(
        video_id,
        video_url,
        json.dumps(metadata),
        json.dumps(transcript),
        "processing",
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
