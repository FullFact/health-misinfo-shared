# Read some CSV files with labelled data, and insert into local db.
# Makes most sense to populate an empty db
import base64
import json
import requests
import pandas as pd


# First run React back end locally, e.g. with:
# PYTHONPATH=src USERS=UUUU:PPPP poetry run python -m raphael_backend_flask.app
# Then put the same username, password below
# Then run this script.
# Might want to call @app.delete("/api/training_claims/<string:id>") for each video id before inserting new data?

REACT_APP_BASE_URL = "http://localhost:3000/api"
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
    """Load/display first few records"""
    url = REACT_APP_BASE_URL + "/all_training_claims"
    response = requests.get(url, headers=headers)
    training = response.json()
    print(f"Found {len(training)} training claims. Last few:")
    for i in range(min(5, len(training))):
        print(training[-i])


def insert_training_claim(video_id: str, claim: str, label: str, offset_s: float):
    """Insert a single training claim"""
    json_data = {
        "video_id": video_id,
        "claim": claim,
        "label": json.dumps(label),
        "offset_s": offset_s,
    }

    response = requests.post(
        REACT_APP_BASE_URL + "/training_claims", json=json_data, headers=headers
    )


def insert_rows_from_file(filename: str) -> None:
    """Read a CSV of annotated data and insert each row as a record in
    the training claims table"""
    df = read_file(filename)
    for _, row in df.iterrows():
        insert_training_claim(
            row.get("video_id", "no_video_id"),
            row["output_text"],
            {"harm": row["harm"], "understandability": row["understandability"]},
            float(row.get("offset_s", 0.0)),
        )


if __name__ == "__main__":

    insert_rows_from_file("data/MVP_labelled_claims_1.csv")
    view_training_claims()
