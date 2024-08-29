import json
from typing import Any, Iterable

from health_misinfo_shared.fine_tuning import (
    infer_transcript_claims,
    infer_multimodal_claims,
)
from raphael_backend_flask import multimodal
from raphael_backend_flask.db import (
    execute_sql,
    update_claim_extraction_run,
)
from health_misinfo_shared.label_scoring import get_claim_summary
from raphael_backend_flask.transcript import refine_offsets


def extract_transcript_claims(run: dict) -> Iterable[dict[str, Any]]:
    sentences = run["transcript"]
    inferred_claims = infer_transcript_claims(sentences)

    for response in inferred_claims:
        claims = response.get("response", {})
        chunk = response.get("chunk")
        if not chunk:
            raise Exception("Could not extract claims: got no chunks")

        for claim in claims:
            labels_dict = claim.get("labels", {})
            labels_dict["summary"] = get_claim_summary(labels_dict)
            parsed_claim = {
                "run_id": run["id"],
                "claim": claim.get("claim", "Probably a bug - please report"),
                "raw_sentence_text": claim.get("original_text", ""),
                "labels": json.dumps(labels_dict),
                "offset_start_s": chunk.get("start_offset", 0),
            }
            end = chunk.get("end_offset")
            if end is not None:
                parsed_claim["offset_end_s"] = end

            parsed_claim = refine_offsets(parsed_claim, sentences)

            execute_sql(
                f"INSERT INTO inferred_claims ({', '.join(parsed_claim.keys())}) VALUES ({', '.join(['?'] * len(parsed_claim))})",
                tuple(parsed_claim.values()),
            )
            parsed_claim["labels"] = labels_dict
            yield parsed_claim

    # Mark transcript done
    update_claim_extraction_run(run["id"], status="complete")


def extract_multimodal_claims(run: dict) -> Iterable[dict[str, Any]]:
    claims = infer_multimodal_claims(multimodal.GCS_BUCKET, run["video_path"])

    for claim in claims:
        labels_dict = claim.get("labels", {})
        labels_dict["summary"] = get_claim_summary(labels_dict)
        timestamp = claim.get("timestamp", {})
        start = timestamp.get("start", 0)
        end = timestamp.get("end", 0)

        # Correct for times often being returned as m.ss rather than just seconds...
        diff = end - start
        if diff < 1 and diff > 0:
            start = start * 60
            end = end * 60

        parsed_claim = {
            "run_id": run["id"],
            "claim": claim.get("claim", "Probably a bug - please report"),
            "raw_sentence_text": claim.get("original_text", ""),
            "labels": json.dumps(labels_dict),
            "offset_start_s": start,
            "offset_end_s": end,
        }

        execute_sql(
            f"INSERT INTO inferred_claims ({', '.join(parsed_claim.keys())}) VALUES ({', '.join(['?'] * len(parsed_claim))})",
            tuple(parsed_claim.values()),
        )
        parsed_claim["labels"] = labels_dict
        yield parsed_claim

    # Mark transcript done
    update_claim_extraction_run(run["id"], status="complete")
