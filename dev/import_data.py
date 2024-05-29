# Read some CSV files with labelled training data, and insert into *local db*.

import base64
import json
import requests
import pandas as pd


BASE_URL = "http://localhost:3000/"
# See the README file for how to start flask development server locally; then set up username & password as specified there.
username = "<REPLACE>"
password = "<REPLACE>"
username = "ff"
password = "changeme"

auth_header = base64.b64encode(f"{username}:{password}".encode()).decode()
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {auth_header}",
}


def read_file(fn: str) -> pd.DataFrame:
    df = pd.read_csv(fn)
    return df


def view_training_claims():
    """Load/display a few records, just to show what's working"""
    url = BASE_URL + "/api/all_training_claims"
    response = requests.get(url, json={}, headers=headers)
    training = response.json()
    print(f"Found {len(training)} training claims. Last few:")
    for i in range(min(5, len(training))):
        print(training[-i])


def insert_training_claim(video_id: str, claim: str, label: str):
    """Insert a single training claim"""
    json_data = {
        "youtube_id": video_id,
        "claim": claim,
        "labels": json.dumps(label),
    }
    try:
        response = requests.post(
            BASE_URL + "api/training_claims", json=json_data, headers=headers
        )
    except Exception as e:
        print("Failed to insert row: ", json_data)
        print(e)


def insert_rows_from_file(filename: str) -> None:
    """Read a CSV of annotated data and insert each row as a record in
    the training claims table"""
    df = read_file(filename)
    for _, row in df.iterrows():
        insert_training_claim(
            row.get("video_id", "no_video_id"),
            row["output_text"],
            {"harm": row["harm"], "understandability": row["understandability"]},
            # float(row.get("offset_s", 0.0)),
        )


if __name__ == "__main__":

    view_training_claims()

    for data_file in [1, 2, 3, 4]:
        insert_rows_from_file(f"data/MVP_labelled_claims_{data_file}.csv")

    view_training_claims()
