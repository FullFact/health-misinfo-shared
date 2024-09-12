import json
import os
import re
import tempfile

import yt_dlp
from google.cloud import storage

from raphael_backend_flask.db import create_multimodal_claim_extraction_run
from raphael_backend_flask.exceptions import FlashException

GCS_BUCKET = "fullfact-nlp"
GCS_FOLDER = "raphael/videos"

# Not used at the moment as we're not restricting multimodal to YouTube
tiktok_url_matcher = re.compile(r"https?://(www\.)?tiktok.com/[^/]+/video/([0-9]+).*")


def handle_multimodal_url(user_id: int, url: str) -> int:
    info = fetch_video(url)
    if not info:
        raise FlashException("Could not process video.")

    title = info.get("title")
    if not title or title.startswith("Video by"):
        desc = info.get("description")
        if desc and len(desc) < 150:
            title = desc

    metadata = {
        "title": title,
        "url": info["webpage_url"],
    }

    return create_multimodal_claim_extraction_run(
        user_id, info["dest"], json.dumps(metadata)
    )


def upload_file_to_gcs(local_filepath: str, bucket_name: str, folder: str) -> str:
    filename = local_filepath.split("/")[-1]
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob_location = os.path.join(folder, filename)
    blob = bucket.blob(blob_location)
    blob.upload_from_filename(local_filepath)
    blob.make_public()
    full_location = bucket_name + "/" + blob_location
    return full_location


def fetch_video(url: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        print("created temporary directory", tmp_dir_name)
        output_path = os.path.join(tmp_dir_name, "%(id)s.%(ext)s")

        opts = {
            "noprogress": True,  # don't print progress
            "outtmpl": output_path,  # use the configured temp dir
            "noplaylist": True,  # don't download playlists
        }
        with yt_dlp.YoutubeDL(opts) as dl:
            info = dl.extract_info(url)

        if not info or not info.get("requested_downloads"):
            raise FlashException("Could not download video")

        downloaded = info["requested_downloads"][0]
        filepath = downloaded["filepath"]
        dest = upload_file_to_gcs(filepath, GCS_BUCKET, GCS_FOLDER)
        info["dest"] = dest
        return info


def is_downloadable(url: str) -> bool:
    opts = {
        "simulate": True,
        "skip_download": True,  # Don't download the video (possibly redundant)
        "noprogress": True,  # don't print progress
        "noplaylist": True,  # playlists aren't valid
    }
    with yt_dlp.YoutubeDL(opts) as dl:
        try:
            info = dl.extract_info(url)
            return bool(info)
        except Exception:
            return False


def valid_multimodal_video_url(url: str) -> bool:
    return is_downloadable(url)
