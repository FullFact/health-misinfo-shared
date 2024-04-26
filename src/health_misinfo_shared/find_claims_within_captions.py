import os
import json
from typing import Iterator, Any

from google.auth import default

import vertexai
from vertexai.language_models import TextGenerationModel


credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-east4"  # NB: Gemini is not available in europe-west2 (yet?)

FIND_HEALTH_CLAIMS_PROMPT = """
I am going to give you the captions for a YouTube video in a JSON formatted string.

You are a health fact checker, trying to identify claims in the video's text.

I would like you to produce a list of all of the health related claims contained within the video.

You should only consider claims that are on health topics including  personal health, public health, medicine, mental health, drugs, treatments or hospitals.

Ignore sentences that are not directly about some aspect of health, and also ignore sentences that make vague statements or are about someone's individual and personal experiences.

It is okay if you do not find any claims. Not every video will have them. Only return a claim if you are confident it is a health related claim.

As well as the original claim, please include a rewording of the claims so they make sense without extra context, while still keeping the meaning the same as in the original text.

Your output should be a json encoded list of dictionaries.

Here is an example of the output format:
[
	{"original_claim": *claim 1*, "reworded_claim": *reworded claim 1*},
	...,
	{"original_claim": *claim n*, "reworded_claim": *reworded claim n*}
]

Your output must be a machine readable json string only.

Here is the video I would like you to process:
""".strip()


def loop_through_videos(video_caption_directory: str) -> Iterator[str]:
    for path, folders, files in os.walk(video_caption_directory):
        # Open file
        for filename in files:
            if not filename.endswith(".json"):
                continue

            with open(os.path.join(path, filename)) as f:
                video = json.load(f)

            video = {
                "video_id": video["video_id"],
                "video_title": video["video_title"],
                "video_text": " ".join(
                    [s["sentence_text"] for s in video["sentences"]]
                ),
            }
            yield json.dumps(video)


def load_model() -> TextGenerationModel:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LLM_LOCATION)
    return TextGenerationModel.from_pretrained("text-bison@002")


def find_health_claims(
    model: TextGenerationModel, video_json_string: str
) -> dict[str, Any] | None:
    prompt = FIND_HEALTH_CLAIMS_PROMPT + "\n" + video_json_string
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 2048,
        "temperature": 0,
        "top_p": 1,
    }
    try:
        response = model.predict(prompt, **parameters)
    except Exception as e:
        print("Model couldn't process video")
        print(e)

    try:
        candidate = response.candidates[0]
        health_claims = json.loads(candidate.text)
        return {
            "video_id": json.loads(video_json_string)["video_id"],
            "safety": candidate.safety_attributes,
            "health_claims": health_claims,
        }

    except Exception as e:
        print(f"Could not handle video.")
        print(e)
        return None


def find_health_claims_for_all_videos(
    caption_directory: str, output_directory: str
) -> None:
    model = load_model()
    for video_string in loop_through_videos(caption_directory):
        health_claims = find_health_claims(model, video_string)
        if health_claims is None:
            continue

        filename = f"health_claims_{health_claims['video_id']}.json"
        with open(os.path.join(output_directory, filename), "w") as out_file:
            json.dump(health_claims, out_file, indent=4)


if __name__ == "__main__":
    find_health_claims_for_all_videos(
        caption_directory="data/captions",
        output_directory="data/health_claims",
    )
