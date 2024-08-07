import json
import pandas as pd

from health_misinfo_shared.prompts import HEALTH_INFER_MULTI_LABEL_PROMPT
from health_misinfo_shared.fine_tuning import construct_in_context_examples
from health_misinfo_shared.label_scoring import get_claim_summary

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

    prompt_no_context = "\n".join([base_prompt, input_text])
    prompt_with_context = "\n".join([base_prompt, in_context_prompt_part, input_text])

    with open("evaluation/prompt_no_context.txt", "w") as out_file:
        out_file.write(prompt_no_context)

    with open("evaluation/prompt_with_context.txt", "w") as out_file:
        out_file.write(prompt_with_context)


def make_tests_file():
    training_data_file = "src/health_misinfo_shared/full_in_context_labelled_data.csv"
    training_data = pd.read_csv(training_data_file)
    training_data.fillna("", inplace=True)

    # generate the test rows
    eval_data = (
        training_data.groupby("input_text")
        .apply(
            lambda sub_df: json.dumps(
                [
                    {
                        "claim": row["output_text"],
                        "original_text": row["output_text"],
                        "labels": {
                            "understandability": row["understandability"],
                            "type_of_claim": row["type_of_claim"],
                            "type_of_medical_claim": row["type_of_medical_claim"],
                            "support": row["support"],
                            "harm": row["harm"],
                            "summary": get_claim_summary(row),
                        },
                    }
                    for idx, row in sub_df.iterrows()
                ],
                indent=4,
            )
        )
        .reset_index()
    )
    eval_data.columns = ["chunk", "expected_output"]

    # add the assertions
    eval_data["__expected1"] = ["is-json"] * eval_data.shape[0]
    eval_data["__expected2"] = [
        "python:file://assert_quotes_contained_in_chunk.py"
    ] * eval_data.shape[0]
    eval_data["__expected3"] = [
        "python:file://assert_evaluation_metrics.py"
    ] * eval_data.shape[0]
    eval_data["__expected4"] = [
        "python:file://assert_check_format.py"
    ] * eval_data.shape[0]

    eval_data.to_csv("evaluation/tests.csv")


if __name__ == "__main__":
    # make a txt file for each prompt
    make_prompts_files()

    # make a tests.csv file with input and expected output for each test
    make_tests_file()
