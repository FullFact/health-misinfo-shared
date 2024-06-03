import json
import pandas as pd

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


def make_tests_file():
    training_data_file = "data/test_eval_data_very_dodgy.csv"
    training_data = pd.read_csv(training_data_file)
    training_data.fillna("", inplace=True)

    # generate the test rows
    eval_data = pd.DataFrame()
    eval_data["chunk"] = training_data["input_text"].unique()

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
