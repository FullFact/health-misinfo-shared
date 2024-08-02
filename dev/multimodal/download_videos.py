import os
import subprocess

VIDEO_DIRECTORY = "data/videos"
VIDEO_LIST = "data/videos/tiktoks.txt"


def download_videos(video_list_path: str, video_directory_path: str):
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


if __name__ == "__main__":
    download_videos(VIDEO_LIST, VIDEO_DIRECTORY)
