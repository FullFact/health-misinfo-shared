import json
from typing import Any, Iterable

from health_misinfo_shared.fine_tuning import infer_claims
from health_misinfo_shared.label_scoring import get_claim_summary
from raphael_backend_flask.db import execute_sql, update_claim_extraction_run
from raphael_backend_flask.process import refine_offsets


def extract_claims(run: dict) -> Iterable[dict[str, Any]]:
    sentences = run["transcript"]
    inferred_claims = infer_claims(run["id"], sentences)

    for response in inferred_claims:
        claims = response.get("response")
        chunk = response.get("chunk")
        for claim in claims:
            labels_dict = claim.get("labels", {})
            labels_dict["summary"] = get_claim_summary(labels_dict)
            # checkworthiness = claim.get("labels", {}).get("summary", "na")
            # checkworthiness will be one of "worth checking", "may be worth checking" or "not worth checking"
            parsed_claim = {
                "run_id": run["id"],
                "claim": claim["claim"],
                "raw_sentence_text": claim["original_text"],
                "labels": json.dumps(labels_dict),
                "offset_start_s": chunk["start_offset"],
            }
            if chunk["end_offset"] is not None:
                parsed_claim["offset_end_s"] = chunk["end_offset"]

            parsed_claim = refine_offsets(parsed_claim, sentences)

            execute_sql(
                f"INSERT INTO inferred_claims ({', '.join(parsed_claim.keys())}) VALUES ({', '.join(['?'] * len(parsed_claim))})",
                tuple(parsed_claim.values()),
            )
            parsed_claim["labels"] = labels_dict
            yield parsed_claim

    # Mark transcript done
    update_claim_extraction_run(run["id"], status="complete")
