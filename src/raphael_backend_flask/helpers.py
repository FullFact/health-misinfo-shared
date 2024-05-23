from urllib.parse import parse_qs, urlparse


def extract_youtube_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return parsed.path[1:]

    if parsed.netloc == "" and len(parsed.path) == 11:
        # if it's 11 chars like a video id, wing it
        return parsed.path

    queries = parse_qs(parsed.query)
    # assume this exists
    return queries["v"][0]
