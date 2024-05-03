# """Access Vertex AI platform"""

import json
import csv
import vertexai

from vertexai.preview.generative_models import GenerativeModel
import vertexai.preview.generative_models as generative_models

from prompts import HEALTH_CLAIM_PROMPT, HEALTH_HARM_PROMPT
from youtube import chunked_transcript

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LOCATION = "us-east4"  # NB: Gemini is not available in europe-west2 (yet?)


def tidy_response(response_text: str) -> str:
    """Strip unnecessary head/tail of response string"""
    # TODO: Maybe use this library instead: https://github.com/noamgat/lm-format-enforcer
    while response_text.startswith("`"):
        response_text = response_text[1:]
    while response_text.endswith("`"):
        response_text = response_text[:-1]
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
    response_text = tidy_response(response.text)  # pyright: ignore
    jsonl_obj = json.loads(response_text)
    return jsonl_obj


def process_video(video_id: str, transcript: list[dict]) -> list[dict]:
    """Take the transcript of a single video and pass it to the LLM.
    Return a list of any claims found."""
    llm_responses = []

    chunks = chunked_transcript(transcript)
    for chunk in chunks:
        try:
            llm_response = generate_reponse(chunk)
            for found_claim in llm_response:
                found_claim["video_id"] = video_id
                found_claim["chunk"] = chunk
                found_claim["offset_ms"] = 0
                llm_responses.append(found_claim)
        except Exception as e:
            # just carry on for now...
            print(e)
            pass
    return llm_responses
