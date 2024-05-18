# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python
# Handy getting-started guide https://developers.google.com/youtube/v3/quickstart/python
# NOTE: the official API does't actually give you captions (unless you own the video), so
# we parse the raw XML file to get a temporary link to the captions and download those.

from html import unescape
import re
from typing import Iterable
import requests


def chunked_transcript(transcript: list[dict]) -> Iterable[str]:
    """Split/merged a list of sentences into series of overlapping text chunks."""

    current_chunk_text = ""
    for sentence in transcript:
        current_chunk_text += sentence["sentence_text"] + " "
        if len(current_chunk_text) > 5000:
            yield current_chunk_text
            # Keep the end of this chunk as the start of the next...
            # ...but remove the first (probably incomplete) word
            current_chunk_text = current_chunk_text[-500:]
            start_idx = current_chunk_text.strip().find(" ")
            current_chunk_text = current_chunk_text[start_idx:]

    yield current_chunk_text


def clean_str(d: dict) -> dict:
    d["sentence_text"] = d["sentence_text"].replace("&amp;#39;", "'")
    return d


urls_re = re.compile('(https://www.youtube.com/api/timedtext[^"]+lang=en)')
caption_re = re.compile(
    r'\<text start="(?P<start>[0-9\.]*?)" dur="[0-9\.]*?">(?P<sentence_text>.*?)</text>'
)


def download_captions(html: str) -> list[dict]:
    # only find URLs with lang=en
    urls = urls_re.findall(html)
    if not len(urls):
        raise Exception

    url = urls[0].replace("\\u0026", "&")

    with requests.get(url, allow_redirects=False, timeout=60) as resp:
        sentence = resp.text

    sentences = [clean_str(m.groupdict()) for m in caption_re.finditer(sentence)]
    return sentences


title_re = re.compile("<title>(.*) - YouTube</title>")


def extract_title(html: str) -> str:
    titles = title_re.findall(html)
    if not len(titles) == 1:
        raise Exception

    return unescape(titles[0])
