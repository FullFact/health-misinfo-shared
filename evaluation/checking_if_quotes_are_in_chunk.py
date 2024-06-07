import os
import json
import random
import pandas as pd

from health_misinfo_shared.youtube_api import get_captions, form_chunks
from health_misinfo_shared.prompts import HEALTH_INFER_MULTI_LABEL_PROMPT
from health_misinfo_shared.fine_tuning import construct_in_context_examples


in_context_examples, eval_examples = construct_in_context_examples(
    [
        "data/MVP_labelled_claims_1.csv",
        "data/MVP_labelled_claims_2.csv",
        "data/MVP_labelled_claims_3.csv",
        "data/MVP_labelled_claims_4.csv",
    ]
)


def make_prompts_files():
    base_prompt = HEALTH_INFER_MULTI_LABEL_PROMPT

    in_context_prompt_part = (
        "\nHere are some examples to learn from:\n" + in_context_examples
    )

    input_text = "```{{chunk}}```"

    prompt_with_context = "\n".join([base_prompt, in_context_prompt_part, input_text])

    with open("evaluation/prompt_with_context.txt", "w") as out_file:
        out_file.write(prompt_with_context)


def load_chunks(video_ids: list[str]) -> list[str]:
    chunks = []
    for video_id in video_ids:
        captions = get_captions(video_id)
        if "sentences" not in captions:
            continue
        current_chunks = [c["text"] for c in form_chunks(captions["sentences"])]
        chunks += current_chunks
    return chunks


def make_tests_file():
    with open("data/known_misinfo/video_ids.json") as id_file:
        video_ids = json.load(id_file)

    chunks = load_chunks(video_ids[:10])
    random.shuffle(chunks)

    # generate the test rows
    eval_data = pd.DataFrame()
    eval_data["chunk"] = chunks[:100]

    # add the assertions
    eval_data["__expected1"] = ["is-json"] * eval_data.shape[0]
    eval_data["__expected2"] = [
        "python:file://assert_quotes_contained_in_chunk.py"
    ] * eval_data.shape[0]

    eval_data.to_csv("evaluation/tests_quote_in_chunk.csv")


if __name__ == "__main__":
    # make a txt file for each prompt
    make_prompts_files()

    # make a tests.csv file with input and expected output for each test
    make_tests_file()
