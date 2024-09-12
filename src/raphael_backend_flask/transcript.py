def refine_offsets(claim: dict, transcript: dict) -> dict:
    # figure out the bit of the transcript that the chunk refers to
    start_idx = 0
    while claim["offset_start_s"] < transcript[start_idx]["start"]:
        start_idx += 1
    if claim.get("offset_end_s") is not None:
        end_idx = start_idx
        while claim["offset_end_s"] > transcript[end_idx]["start"]:
            end_idx += 1
    else:
        end_idx = len(transcript)

    # refine the end of the chunk
    chunk_text = ""
    for end_idx, sentence in enumerate(transcript[start_idx:end_idx], start_idx + 1):
        chunk_text += sentence["sentence_text"] + " "
        if claim["raw_sentence_text"] in chunk_text:
            break
    else:
        # Error! Couldn’t find raw sentence in transcript.
        # This means the LLM is not returning the raw sentence text.
        return claim

    # refine the start of the chunk
    chunk_text = ""
    for diff, sentence in enumerate(reversed(transcript[start_idx:end_idx])):
        chunk_text = sentence["sentence_text"] + " " + chunk_text
        if claim["raw_sentence_text"] in chunk_text:
            break
    start_idx = end_idx - 1 - diff

    # update the claim with the refined offsets
    claim["offset_start_s"] = transcript[start_idx]["start"]
    if end_idx < len(transcript):
        claim["offset_end_s"] = transcript[end_idx]["start"]
    return claim
