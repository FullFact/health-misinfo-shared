# Pass a set of videos through the app.
# Handy for end-to-end testing or populating an empty database.
# import base64
# import requests
from flask import (
    jsonify,
    redirect,
    request,
    url_for,
)
from raphael_backend_flask.routes import post_youtube_url

# REACT_APP_BASE_URL = "http://localhost:3000/api"
# username = "ff"
# password = "changeme"
# auth_header = base64.b64encode(f"{username}:{password}".encode()).decode()
# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Basic {auth_header}",
# }


def process_video(video_id: str):
    # url = REACT_APP_BASE_URL + "/transcripts"

    # response = requests.post(url, json={"id": video_id}, headers=headers)
    # print("Processed video: ", response.json())
    post_youtube_url()


if __name__ == "__main__":
    misinfo_vids = [
        "NhX4YyWIbqQ",
        "lbzn5iz8Mbo",
        "AlUNBHMDoIw",
        "giTorcCLWPE",
        "4DWKf5RqU-s",
        "BQmb4-og4IU",
    ]

    [process_video(vid) for vid in misinfo_vids]
