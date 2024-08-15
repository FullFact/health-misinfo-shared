# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python
# Handy getting-started guide https://developers.google.com/youtube/v3/quickstart/python
# NOTE: the official API does't actually give you captions (unless you own the video), so
# we parse the raw HTML file to get a temporary link to the captions and download those.

import re
from html import unescape
from urllib.parse import parse_qs, urlparse

import requests

from health_misinfo_shared.youtube_api import clean_str

urls_re = re.compile(r'https://www.youtube.com/api/timedtext[^"]+lang=en[^"]*')
caption_re = re.compile(
    r'<text start="(?P<start>[0-9\.]*?)" dur="[0-9\.]*?">(?P<sentence_text>[^<]*)<\/text>'
)


def download_captions(html: str) -> list[dict]:
    # only find english language caption URLs
    urls = urls_re.findall(html)
    if not len(urls):
        raise Exception("Couldn’t extract captions for that video")

    url = urls[0].replace("\\u0026", "&")

    with requests.get(url, allow_redirects=False, timeout=60) as resp:
        sentence = resp.text

    sentences = [clean_str(m.groupdict()) for m in caption_re.finditer(sentence)]
    return sentences


title_re = re.compile("<title>(.*) - YouTube</title>")


def extract_title(html: str) -> str:
    titles = title_re.findall(html)
    if len(titles) != 1:
        raise Exception("Couldn’t extract a title for that video")

    return unescape(titles[0])


def extract_youtube_id(url: str) -> str:
    def check_id_length(youtube_id: str) -> str:
        # YouTube video IDs are 11 characters
        if len(youtube_id) != 11:
            raise Exception("Not a valid YouTube video ID")
        return youtube_id

    parsed = urlparse(url)
    if parsed.netloc == "youtu.be":
        return check_id_length(parsed.path[1:])

    if parsed.netloc == "":
        return check_id_length(parsed.path)

    queries = parse_qs(parsed.query)
    return check_id_length(queries["v"][0])
