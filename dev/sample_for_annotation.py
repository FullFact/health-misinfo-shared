# Sample a set of YT videos for manual annotation / evaluation
import csv
from health_misinfo_shared.youtube_api import get_captions
from health_misinfo_shared.fine_tuning import infer_transcript_claims
from health_misinfo_shared.label_scoring import calculate_claim_summary_score


def get_transcript_from_YT(video_id: str):
    transcript = get_captions(video_id, "", "")
    return transcript


def add_scores_to_transcript(transcript: list[dict]) -> list[dict]:
    """Process a transcript via genAI and insert the score for each claim found."""
    # Transcript should be list of dicts with keys ["sentence_text", "start"]

    # get generator of {"response": claims, "chunk": chunk} items:
    responses = infer_transcript_claims(transcript["sentences"])
    for chunk in responses:
        for claim in chunk["response"]:
            print(claim.get("original_text"))  # seems to always return 'not found'?
            labels = claim.get("labels", {})
            score = calculate_claim_summary_score(labels)
            claim["score"] = score
        yield chunk


def write_scores(
    prefix: list[str], scored_transcript: list[dict], filename: str
) -> None:
    """Extracted phrases and scores from transcript and write to CSV.
    Prefix is a list of cells to prefix to each row"""
    chunks = 0
    claims = 0
    with open(filename, "wt", encoding="utf-8") as fout:
        csv_writer = csv.writer(fout, quoting=csv.QUOTE_ALL)
        for chunk in scored_transcript:
            chunks += 1
            for claim in chunk["response"]:
                claims += 1
                csv_writer.writerow(
                    [*prefix, claim["claim"], claim["score"], claim["original_text"]]
                )
    print(f"Wrote scores for {claims=} found in {chunks=}")


if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=o5fOZBo3iWo&pp=ygUSb2xpdmUgb2lsIGJlbmVmaXRz"
    for video_id in ["o5fOZBo3iWo", "MrjIXLQ_OdA", "pPmNN__GZyM"]:
        print(f"\n{'='*50}{video_id}{'='*50}")
        filename_out = f"scored_{video_id}.csv"
        prefix = [video_id]
        transcript = get_transcript_from_YT(video_id)
        scored_transcript = add_scores_to_transcript(transcript)
        write_scores(prefix, scored_transcript, filename_out)
