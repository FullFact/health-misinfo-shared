from io import StringIO
import json
import re
from html import unescape
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

import requests
import yt_dlp
import webvtt

from raphael_backend_flask.db import create_youtube_claim_extraction_run
from raphael_backend_flask.exceptions import FlashException

title_re = re.compile("<title>(.*) - YouTube</title>")
urls_re = re.compile('(https://www.youtube.com/api/timedtext[^"]+lang=en)')
caption_re = re.compile(
    r'<text start="(?P<start>[0-9\.]*?)" dur="[0-9\.]*?">(?P<sentence_text>[^<]*)<\/text>'
)


def _remove_overlap(
    source: list[Any], compare: list[Any], key: Callable[[Any], Any] = lambda x: x
) -> list[Any]:
    if not compare or not source:
        return source

    max_overlap = min(len(source), len(compare))
    for i in range(1, max_overlap + 1):
        if [key(x) for x in source[:i]] == [key(x) for x in compare[-i:]]:
            return source[i:]
    return source


def download_captions(url: str) -> list[dict]:
    resp = requests.get(url)
    resp.raise_for_status()

    subtitles: list[dict] = []
    for block in webvtt.read_buffer(StringIO(resp.text)).captions:
        text = re.sub(r"<[^>]+>", "", block.text)
        lines = (line for line in text.splitlines() if line.strip())
        captions = [
            {"sentence_text": line, "start": int(block.start_in_seconds)}
            for line in lines
        ]
        captions = _remove_overlap(
            captions, subtitles, key=lambda s: s["sentence_text"]
        )
        subtitles.extend(captions)
    return subtitles


def handle_youtube_query(user_id: int, id_or_url: str) -> int:
    youtube_id = extract_youtube_id(id_or_url)
    youtube_url = f"https://youtube.com/watch?v={youtube_id}"

    opts = {
        "verbose": True,
        "allowed_extractors": ["youtube$"],  # Only allow videos & lives
        "format": "ba[filesize<2M] / ba[filesize<5M] / wa / wa*",  # lowest size formats :)
        "skip_download": True,  # Don't download the video (possibly redundant)
        "writeautomaticsub": True,
        "subtitleslangs": [".*orig"],  # Download subtitles only in original language
        "subtitlesformat": "vtt",  # Force VTT subtitles
        # "quiet": True,  # Shut up
        # "no_warnings": True,  # actually, commenting this out
        "noprogress": True,  # don't print progress
        "sleep_interval": 10.0,
        "max_sleep_interval": 20.0,
        "sleep_interval_requests": 1,
        "sleep_interval_subtitles": 5,
        "extractor_args": {
            "youtube": {
                "player_client": ["web_embedded"],
            },
        },
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        res = ydl.extract_info(youtube_url, download=False)
        if not isinstance(res, dict):
            return False
        title = res["title"]
        captions_url = str(res["requested_subtitles"]["en-orig"]["url"])

    metadata = {"title": title}
    transcript = download_captions(captions_url)

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
