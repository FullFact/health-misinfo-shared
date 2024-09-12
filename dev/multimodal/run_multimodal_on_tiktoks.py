import os
import json
from typing import Iterator
from google.cloud import storage

from multimodal.multimodal_analyser import MultiModalRaphael


GCS_BUCKET = "fullfact-nlp"
GCS_FOLDER = "raphael/videos"

OUT_PATH = "data/videos/analysed.json"


def get_mp4s(bucket_name: str, folder_name: str) -> Iterator[str]:
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob_list = bucket.list_blobs(prefix=folder_name)
    for blob in blob_list:
        blob_name: str = blob.name
        if blob_name.endswith(".mp4"):
            yield f"gs://{os.path.join(bucket_name, blob_name)}"


def analyse_tiktoks(gcs_bucket: str, gcs_folder: str, out_path: str) -> None:
    analyser = MultiModalRaphael()
    analysed = [analyser.analyse_video(mp4) for mp4 in get_mp4s(gcs_bucket, gcs_folder)]
    with open(out_path, "w") as out_file:
        json.dump(analysed, out_file, indent=4)


if __name__ == "__main__":
    analyse_tiktoks(GCS_BUCKET, GCS_FOLDER, OUT_PATH)
