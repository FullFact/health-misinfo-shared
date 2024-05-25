import json
from typing import Generator

import requests

from health_misinfo_shared.vertex import process_video
from raphael_backend_flask.db import (
    create_video_transcript,
    execute_sql,
    update_video_transcript,
)
from raphael_backend_flask.youtube import download_captions, extract_title


def download_transcript(youtube_id: str) -> int:
    youtube_url = f"https://youtube.com/watch?v={youtube_id}"
    with requests.get(youtube_url, timeout=60) as resp:
        resp.raise_for_status()
        video_html = resp.text

    title = extract_title(video_html)
    metadata = {"title": title}
    transcript = download_captions(video_html)

    # Add transcript text
    return create_video_transcript(
        youtube_id,
        json.dumps(metadata),
        json.dumps(transcript),
    )


def extract_claims(run: dict) -> Generator:
    sentences = json.loads(run["transcript"])
    claims = process_video(run["id"], sentences)

    for claim in claims:
        claim["raw_sentence_text"] = claim["sentence"]
        execute_sql(
            "INSERT INTO inferred_claims (run_id, claim, raw_sentence_text, label, offset_start_s, offset_end_s) VALUES (?, ?, ?, ?, ?, ?)",
            (
                run["id"],
                claim["claim"],
                claim["raw_sentence_text"],
                "health",
                claim["offset_start_s"],
                claim["offset_end_s"],
            ),
        )
        yield claim

    # Mark transcript done
    update_video_transcript(run["id"], status="completed")
