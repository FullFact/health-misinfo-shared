# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python
# Handy getting-started guide https://developers.google.com/youtube/v3/quickstart/python
# NOTE: the official API does't actually give you captions (unless you own the video), so
# we parse the raw XML file to get a temporary link to the captions and download those.

import re
from html import unescape

import requests

from health_misinfo_shared.youtube_api import clean_str

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
