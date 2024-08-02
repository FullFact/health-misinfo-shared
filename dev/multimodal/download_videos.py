import os
import subprocess

from google.cloud import storage

VIDEO_DIRECTORY = "data/videos"
VIDEO_LIST = "data/videos/tiktoks.txt"
GCS_BUCKET = "fullfact-nlp"
GCS_FOLDER = "raphael/videos"


def upload_file_to_gcs(local_filepath: str, bucket: str, folder: str) -> None:
    filename = local_filepath.split("/")[-1]
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket)
    blob_location = os.path.join(folder, filename)
    blob = bucket.blob(blob_location)

    generation_match_precondition = 0
    blob.upload_from_filename(
        local_filepath, if_generation_match=generation_match_precondition
    )


def download_videos(
    video_list_path: str,
    video_directory_path: str,
    gcs_bucket: str,
    gcs_folder: str,
):
    with open(video_list_path) as video_list_file:
        video_list = [line.strip() for line in video_list_file]

    for video_url in video_list:
        uid = video_url.strip("/").split("/")[-1]
        out_path = os.path.join(video_directory_path, f"{uid}.mp4")
        if os.path.exists(out_path):
            continue
        command = f'yt-dlp "{video_url}" -o "{out_path}"'
        print(command)
        subprocess.run(command, shell=True)

        upload_file_to_gcs(out_path, gcs_bucket, gcs_folder)


if __name__ == "__main__":
    download_videos(VIDEO_LIST, VIDEO_DIRECTORY, GCS_BUCKET, GCS_FOLDER)
