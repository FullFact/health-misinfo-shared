import json
from typing import Any, Iterable

import requests

from health_misinfo_shared.fine_tuning import infer_claims
from raphael_backend_flask.db import (
    create_claim_extraction_run,
    execute_sql,
    update_claim_extraction_run,
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
    return create_claim_extraction_run(
        youtube_id,
        json.dumps(metadata),
        json.dumps(transcript),
    )


def extract_claims(run: dict) -> Iterable[dict[str, Any]]:
    sentences = json.loads(run["transcript"])
    inferred_claims = infer_claims(run["id"], sentences)

    for response in inferred_claims:
        claims = response.get("response")
        chunk = response.get("chunk")
        for claim in claims:
            label_str = json.dumps(claim.get("labels", {}))
            checkworthiness = claim.get("labels", {}).get("summary", "na")
            # checkworthiness will be one of "worth checking", "may be worth checking" or "not worth checking"
            parsed_claim = {
                "run_id": run["id"],
                "claim": f"({checkworthiness}) " + claim["claim"],
                "raw_sentence_text": chunk["text"],
                "label": label_str,
                "offset_start_s": float(chunk["start_offset"]),
                "offset_end_s": float(chunk["end_offset"]),
            }
            execute_sql(
                "INSERT INTO inferred_claims (run_id, claim, raw_sentence_text, label, offset_start_s, offset_end_s) VALUES (?, ?, ?, ?, ?, ?)",
                tuple(parsed_claim.values()),
            )
            yield parsed_claim

    # Mark transcript done
    update_claim_extraction_run(run["id"], status="complete")
