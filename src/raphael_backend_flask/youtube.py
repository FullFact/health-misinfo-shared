import json
import re
from html import unescape
from urllib.parse import parse_qs, urlparse

import requests

from health_misinfo_shared.youtube_api import clean_str
from raphael_backend_flask.db import create_youtube_claim_extraction_run
from raphael_backend_flask.exceptions import FlashException

title_re = re.compile("<title>(.*) - YouTube</title>")
urls_re = re.compile('(https://www.youtube.com/api/timedtext[^"]+lang=en)')
caption_re = re.compile(
    r'<text start="(?P<start>[0-9\.]*?)" dur="[0-9\.]*?">(?P<sentence_text>[^<]*)<\/text>'
)


def download_captions(html: str) -> list[dict]:
    # only find URLs with lang=en
    urls = urls_re.findall(html)
    if not len(urls):
        raise Exception("Couldn’t extract captions for that video")

    url = urls[0].replace("\\u0026", "&")

    with requests.get(url, allow_redirects=False, timeout=60) as resp:
        sentence = resp.text

    sentences = [clean_str(m.groupdict()) for m in caption_re.finditer(sentence)]
    return sentences


def handle_youtube_query(user_id: int, id_or_url: str) -> int:
    youtube_id = extract_youtube_id(id_or_url)
    youtube_url = f"https://youtube.com/watch?v={youtube_id}"
    with requests.get(youtube_url, timeout=60) as resp:
        resp.raise_for_status()
        video_html = resp.text

    title = extract_title(video_html)
    metadata = {"title": title}
    transcript = download_captions(video_html)

    claim_extraction_run_id = create_youtube_claim_extraction_run(
        user_id,
        youtube_id,
        json.dumps(metadata),
        json.dumps(transcript),
    )
    return claim_extraction_run_id


def extract_title(html: str) -> str:
    titles = title_re.findall(html)
    if len(titles) != 1:
        raise FlashException("Couldn’t extract a title for that video")
    return unescape(titles[0])


def extract_youtube_id(url: str) -> str:
    def check_id_length(youtube_id: str) -> str:
        # YouTube video IDs are 11 characters
        if len(youtube_id) != 11:
            raise FlashException("Not a valid YouTube video ID")
        return youtube_id

    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return check_id_length(parsed.path[1:])

    if parsed.netloc == "":
        return check_id_length(parsed.path)

    queries = parse_qs(parsed.query)
    return check_id_length(queries["v"][0])


def valid_youtube_video_query(query: str) -> bool:
    try:
        extract_youtube_id(query)
        return True
    except Exception:
        return False
