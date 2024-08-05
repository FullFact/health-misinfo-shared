import os
import json
from typing import Iterator
from google.cloud import storage

from gemini import GeminiModel
from prompts import MULTIMODAL_RAPHAEL_PROMPT

from health_misinfo_shared.data_parsing import parse_model_json_output


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


def run_video_through_analysis(model: GeminiModel, video_uri: str) -> str:
    model_output = model.run_prompt_on_video(MULTIMODAL_RAPHAEL_PROMPT, video_uri)
    output_dict = parse_model_json_output(model_output)
    return output_dict


def analyse_tiktoks(gcs_bucket: str, gcs_folder: str, out_path: str):
    model = GeminiModel()
    analysed = [
        run_video_through_analysis(model, mp4)
        for mp4 in get_mp4s(GCS_BUCKET, GCS_FOLDER)
    ]
    with open(out_path, "w") as out_file:
        json.dump(analysed, out_file)


if __name__ == "__main__":
    analyse_tiktoks(GCS_BUCKET, GCS_FOLDER, OUT_PATH)
