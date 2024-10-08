# Sample Python code for youtube.search.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python
# Handy getting-started guide https://developers.google.com/youtube/v3/quickstart/python
# NOTE: the official API does't actually give you captions (unless you own the video), so
# we parse the raw XML file to get a temporary link to the captions and download those.

import json
import os
import re
import string
from pathlib import Path
from typing import Iterable

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
from langdetect import detect

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
YT_CREDENTIALS = None


def clean_str(d: dict) -> dict:
    d["sentence_text"] = d["sentence_text"].replace("&amp;#39;", "'")
    d["start"] = float(d["start"])
    return d


def mostly_english(sentences):
    """Quick check to see if most sentences are probably English"""
    en_count = 0
    for s in sentences:
        try:
            en_count += detect(s["sentence_text"]) == "en"
        except:
            # ignore errors in language detection - can happen with empty/trivial strings
            pass
    return en_count > (0.5 * len(sentences))


def get_captions(
    video_id: str,
    video_title: str | None = None,
    query: str | None = None,
) -> dict:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    r = requests.get(video_url, allow_redirects=False, timeout=60)
    merged_transcripts = {}

    try:
        # Q&D regex to get captions URL from XML-formatted response:
        pat = re.compile(r"(https://www.youtube.com/api/timedtext\?.*?)\"")
        captions_URLs = pat.findall(r.text)
        for captions_URL in captions_URLs:
            captions_URL = captions_URL.replace("\\u0026", "&")

            r = requests.get(captions_URL, allow_redirects=False, timeout=60)

            # extract timestamp and text for each sentence into a dict:
            pat = re.compile(
                r'<text start="(?P<start>[0-9\.]*?)" dur="[0-9\.]*?">(?P<sentence_text>[^<]*)<\/text>'
            )
            transcript = {
                "video_id": video_id,
                "video_title": video_title,
                "search_query": query,
                "sentences": [clean_str(m.groupdict()) for m in pat.finditer(r.text)],
            }
            if mostly_english(transcript["sentences"]) or len(merged_transcripts) == 0:
                # keep English if we find them, else just the first set we find
                merged_transcripts.update(transcript)
    except Exception as e:
        print(f"Failed to get captions from {video_id}")
        print(e)
        # return None
    return merged_transcripts


def load_captions(video_id: str, folder) -> dict:
    """Load captions from local file in a given folder"""
    try:
        with open(
            f"data/captions/{folder}/{video_id}.json", "rt", encoding="utf-8"
        ) as fin:
            captions = json.load(fin)
    except FileNotFoundError:
        captions = dict()
    return captions


def load_texts(folder) -> list[dict]:
    """Reload captions from given local file cache for a query and form
    a list of sentences with text, start-time and video-id"""
    flat_list = []
    for filename in os.listdir(f"data/captions/{folder}"):
        vid_cap = load_captions(filename.replace(".json", ""), folder)
        flat_list.append(
            [
                dict(sentence, video_id=vid_cap["video_id"])
                for sentence in vid_cap["sentences"]
            ]
        )

    return flat_list


def form_chunks(transcript: list[dict]) -> Iterable[dict]:
    """Split/merged a list of sentences into series of overlapping text chunks.
    Each chunk is a dict containing the text and the start/end timestamps"""

    def chunk_length(chunk: list[dict]) -> int:
        return sum((len(c["sentence_text"]) for c in chunk))

    # chunks are at most this many characters long
    max_chunk_size = 1500
    # chunks have at most this many characters of overlap
    overlap_size = 500

    current_chunk = []
    for sentence in transcript:
        if (
            current_chunk
            and chunk_length(current_chunk) + len(sentence["sentence_text"])
            > max_chunk_size
        ):
            yield {
                "text": " ".join((c["sentence_text"] for c in current_chunk)),
                "start_offset": current_chunk[0]["start"],
                "end_offset": sentence["start"],
            }
            while chunk_length(current_chunk) > overlap_size:
                # discard sentences from the start, until the chunk has
                # fewer than `overlap_size` characters
                current_chunk = current_chunk[1:]
        current_chunk.append(sentence)
    if current_chunk:
        yield {
            "text": " ".join((c["sentence_text"] for c in current_chunk)),
            "start_offset": current_chunk[0]["start"],
            "end_offset": None,
        }


def download_captions(
    video_id: str,
    folder: str,
    video_title: str | None = None,
    query: str | None = None,
) -> None:
    """Check if transcript for this video already exists in this folder.
    If not, try and download it there."""
    existing_captions = load_captions(video_id, folder)
    already_exists = len(existing_captions.get("sentences", [])) > 0
    if not already_exists:
        captions = get_captions(video_id, video_title=video_title, query=query)
        # captions['sentences'] is a list of dicts {"start": <offset, seconds>, "sentence_text": <text>}
        if captions:
            target_dir = f"data/captions/{folder}"
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            with open(
                f"{target_dir}/{video_id}.json",
                "wt",
                encoding="utf-8",
            ) as fout:
                json.dump(captions, fout, indent=4)
    else:
        print(
            f"Already had {len(existing_captions.get('sentences', []))} sentences from {video_id}"
        )

    # NOTE: the follow approach doesn't work as the captions API can't access other people's videos
    # caption_request = youtube.captions().list(part="snippet", videoId=video_id)
    # request = youtube.captions().download(id=caption_id)
    # download = MediaIoBaseDownload(fh, request)


def search_for_captions(query: str, folder: str):
    """Pass query into YouTube's search API, and store any available
    captions in the specified folder, one file per video."""

    # Disable OAuthlib's HTTPS verification when running locally.
    # TODO *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = os.environ["CLIENT_SECRETS_FILE"]

    # Get credentials and create an API client
    global YT_CREDENTIALS
    if YT_CREDENTIALS is None:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        YT_CREDENTIALS = flow.run_local_server()  # opens browser for authentication
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=YT_CREDENTIALS
    )

    request = youtube.search().list(
        part="snippet",
        maxResults=10,
        q=query,
        type="video",
        videoCaption="closedCaption",
        relevanceLanguage="en",
        safeSearch="none",
        # topicId="/m/0kt51,/m/019_rr",
    )
    response = request.execute()

    for video in response["items"]:
        video_id = video.get("id").get("videoId")
        video_title = video.get("snippet", {}).get("title")
        print(video_title)
        download_captions(video_id, folder, video_title=video_title, query=query)


def download_captions_of_known_bad_health_vids():
    """A hand-curated list of videos that we (Kate, mostly!) think have bad information"""
    video_ids = [
        "o9AEPKn4MMI",
        "K1EbMbXpjs0",
        "Z0_ulRoJFLg",
        "xOsAwyH2lLc",
        "Hrv01WYjqtU",
        "2508ZPcN9PM",
        "Ih5cz-Qwa6U",
        "FU7r3yGjjWc",
        "ZVkpQKRgHvU",
    ]
    for video_id in video_ids:
        download_captions(video_id, "known_bad")


def query_to_filename(query: str) -> str:
    to_keep = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    return "".join(filter(lambda x: x in to_keep, query.replace(" ", "_")))


def multi_issue_search():
    """Collect a fairly random set of videos across a range of health topics"""
    conditions = [
        "HPV",
        "ADHD",
        "prostate cancer",
        "acne",
        "weight loss",
        "heart disease",
        "STD",
        "STI",
        "menopause",
        "eating disorders",
        "HIV",
        "AIDS",
        "pregnancy",
        "cancer",
        "anorexia",
        "bulimia",
        "proana",
        "promia",
        "diabetes",
        "epilepsy",
        "hypertension",
        "H1N1",
        "Zika",
        "Ebola",
        "psoriasis",
    ]

    things = [
        "vaping",
        "smoking",
        "vaccines",
        "dieting",
        "marijuana",
        "Ozempic",
        "opioids",
        "chiropracty",
        "homeopathy",
        "Oxycodene",
        "Oxycontin",
        "Percocet",
        "MMR",
        "BMI",
    ]

    universal_queries = [
        '"We\'ve all been wrong about" {keyword}',
        '"your doctor doesn\'t want you to know about" {keyword}',
        '"your doctor isn\'t telling you about" {keyword}',
        '"your doctor doesn\'t tell you about" {keyword}',
        '{keyword} "secrets revealed"',
        '"The shocking truth behind" {keyword}',
        '"The truth about" {keyword}',
        '"we don’t talk about" {keyword}',
        '"we’ve all been wrong about" {keyword}',
        "{keyword} exposed",
    ]

    conditions_queries = [
        '{keyword} "natural remedies"',
        '"The real cure for" {keyword}',
        '{keyword} "hacks"',
    ]

    things_queries = [
        '{keyword} "for a month. Here\'s what happened"',
    ]

    for keyword in conditions:
        folder = query_to_filename(keyword)
        for phrase in universal_queries + conditions_queries:
            query = phrase.format(keyword=keyword)
            search_for_captions(query, folder)

    for keyword in things:
        folder = query_to_filename(keyword)
        for phrase in universal_queries + things_queries:
            query = phrase.format(keyword=keyword)
            search_for_captions(query, folder)


if __name__ == "__main__":
    # multi_issue_search()
    # print()

    download_captions("o9AEPKn4MMI", "dc_test_timestamp")
