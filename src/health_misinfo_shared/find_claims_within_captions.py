import os
import json
import time
from typing import Iterator, Any

import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.generative_models import GenerativeModel, Part

from health_misinfo_shared.prompts import TRAINING_SET_HEALTH_CLAIMS_PROMPT
from health_misinfo_shared.data_parsing import parse_model_json_output


GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-east1"  # NB: Gemini is not available in europe-west2 (yet?)

MODEL_PER_MINUTE_QUOTA = {
    "gemini-1.5-pro-preview-0409": 5,
    "gemini-1.0-pro": 300,
}

MODEL_PER_1000_CHARS_COST = {
    "input": {
        "gemini-1.5-pro-preview-0409": 0.000125,
        "gemini-1.0-pro": 0.000375,
    },
    "output": {
        "gemini-1.5-pro-preview-0409": 0.0025,
        "gemini-1.0-pro": 0.0075,
    },
}

CUM_PRICE: int = 0

CURRENT_MODEL = "gemini-1.0-pro"


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


def load_model() -> GenerativeModel:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LLM_LOCATION)
    return GenerativeModel(model_name=CURRENT_MODEL)


def print_info(video_id: str, input_str: str, output_str: str) -> None:
    in_chars = len(input_str)
    out_chars = len(output_str)

    in_price = in_chars / 1000 * MODEL_PER_1000_CHARS_COST["input"][CURRENT_MODEL]
    out_price = out_chars / 1000 * MODEL_PER_1000_CHARS_COST["output"][CURRENT_MODEL]
    price = in_price + out_price

    global CUM_PRICE
    CUM_PRICE += price
    print(f"{video_id} - ${price:.2f} - TOTAL: {CUM_PRICE:.2f}")


def find_health_claims(
    model: GenerativeModel, video_json_string: str
) -> dict[str, Any] | None:
    prompt = TRAINING_SET_HEALTH_CLAIMS_PROMPT + "\n" + video_json_string
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 8192,
        "temperature": 0,
        "top_p": 1,
    }
    try:
        response = model.generate_content(prompt, generation_config=parameters)
    except Exception as e:
        print("Model couldn't process video")
        print(e)
        return None

    try:
        candidate = response.candidates[0]
        video_id = json.loads(video_json_string)["video_id"]
        print_info(video_id, prompt, candidate.text)
        health_claims = parse_model_json_output(candidate.text)
        return {
            "video_id": video_id,
            # "safety": candidate.safety_attributes,
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
        video_id = json.loads(video_string)["video_id"]
        filename = f"health_claims_{video_id}.json"

        if os.path.exists(os.path.join(output_directory, filename)):
            print(f"Already processed {video_id}")
            continue

        health_claims = find_health_claims(model, video_string)

        time.sleep(60 / MODEL_PER_MINUTE_QUOTA[CURRENT_MODEL])  # avoid rate limiting
        if health_claims is None:
            continue

        with open(os.path.join(output_directory, filename), "w") as out_file:
            json.dump(health_claims, out_file, indent=4)


if __name__ == "__main__":
    find_health_claims_for_all_videos(
        caption_directory="data/captions",
        output_directory="data/health_claims",
    )
