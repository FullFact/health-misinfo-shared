"""Access Vertex AI platform"""

import json
import csv
import time
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models
import youtube_api
from prompts import HEALTH_CLAIM_PROMPT, HEALTH_HARM_PROMPT

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LOCATION = "us-east4"  # NB: Gemini is not available in europe-west2 (yet?)


def tidy_response(response_text: str) -> str:
    """Strip unnecessary head/tail of response string"""
    # TODO: Maybe investigate this library instead: https://github.com/noamgat/lm-format-enforcer
    response_text = response_text.strip(" `'\".")
    if response_text.startswith("json"):
        response_text = response_text[5:]
    return response_text


def generate_reponse(transcript: str) -> list[dict]:
    """Pass prompt (inc. transcript) to Vertex AI and process result"""
    # Initialize Vertex AI
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LOCATION)
    # Load the model
    gemini_pro_model = GenerativeModel("gemini-pro")

    # For alternative model:
    # model = TextGenerationModel.from_pretrained("text-bison")
    # response = model.predict(prompt)

    prompt = f"{HEALTH_CLAIM_PROMPT}\n```{transcript}```"
    safety_settings = {
        generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }
    generation_config = {"max_output_tokens": 2048, "temperature": 0.1, "top_p": 0.25}
    response = gemini_pro_model.generate_content(
        prompt, safety_settings=safety_settings, generation_config=generation_config
    )
    response_text = tidy_response(response.text)
    jsonl_obj = json.loads(response_text)
    return jsonl_obj


def process_video(transcript: dict) -> list[dict]:
    """Take the transcript of a single video and pass it to the LLM.
    Return a list of any claims found."""
    video_id = transcript[0].get("video_id")
    llm_responses = []

    chunks = youtube_api.form_chunks(transcript)
    for _id, chunk in enumerate(chunks):
        try:
            llm_response = generate_reponse(chunk)
            for found_claim in llm_response:
                found_claim["video_id"] = video_id
                found_claim["chunk"] = chunk
                llm_responses.append(found_claim)
        except Exception as e:
            # just carry on for now...
            print(e)
    return llm_responses


def generate_training_set(folders: list[str], label: str):
    """Read cached versions of video transcripts from a given list of folders.
    Divide into overlapping chunks and through a pretrained LLM. Ask it to find
    health claims. Put them in a spreadsheet to be manually labelled (for later
    fine-tuning)."""
    all_responses = []
    for folder in folders:
        all_videos_in_folder = youtube_api.load_texts(folder)
        for video in all_videos_in_folder:
            if len(video) == 0:
                print(f"Nothing in {video} !")
                continue
            # video_id = video[0].get("video_id")

            claims = process_video(video)
            all_responses.extend(claims)

            with open(f"llm_responses_{label}.jsonl", "wt", encoding="utf-8") as fout:
                json.dump(all_responses, fout)
            with open(f"llm_responses_{label}.csv", "wt", encoding="utf-8") as f:
                title = ["claim", "sentence", "video_id", "chunk"]
                cw = csv.DictWriter(f, title, quoting=csv.QUOTE_ALL)
                cw.writeheader()
                cw.writerows(all_responses)

            print("<", end="")
            time.sleep(10)  # slow things down a bit to avoid time-outs
            print("> ", end="")


if __name__ == "__main__":
    # These folders are generated by the youtube_api/mutli_issue_search() function
    _folders = [
        "ADHD_nat_rem",
        "HPV_nat_rem",
        "acne_nat_rem",
        "prostate_cancer_nat_rem",
        "weight_loss_nat_rem",
    ]
    generate_training_set(_folders, label="natural_remedies_x5")