# Code originally from https://cloud.google.com/vertex-ai/docs/generative-ai/models/tune-text-models-supervised?hl=en#generative-ai-tune-model-python_vertex_ai_sdk
# Though had a few issues with it..ascii

from __future__ import annotations
from typing import Optional
import json
import pandas as pd
from google.auth import default
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.preview.language_models import TuningEvaluationSpec

from health_misinfo_shared.prompts import (
    HEALTH_CLAIM_PROMPT,
    HEALTH_TRAINING_PROMPT,
    HEALTH_TRAINING_EXPLAIN_PROMPT,
)
from health_misinfo_shared import youtube_api
from health_misinfo_shared.vertex import tidy_response

credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-east4"  # NB: Gemini is not available in europe-west2 (yet?)
GCP_TUNED_MODEL_LOCATION = "europe-west4"  # where we do fine tuning/model storage
CHECKWORTHY_EXPLANATIONS = ["high harm", "citation", "low harm"]
UNCHECKWORTHY_EXPLANATIONS = ["nothing to check", "hedged claim"]
VALID_EXPLANATIONS = CHECKWORTHY_EXPLANATIONS + UNCHECKWORTHY_EXPLANATIONS


def tuning(
    model_display_name: str,
    training_data: pd.DataFrame | str,
    train_steps: int = 10,
    evaluation_dataset: Optional[str] = None,
    tensorboard_instance_name: Optional[str] = None,
) -> TextGenerationModel:
    """Tune a new model, based on a prompt-response data.

    "training_data" can be either the GCS URI of a file formatted in JSONL format
    (for example: training_data=f'gs://{bucket}/{filename}.jsonl'), or a pandas
    DataFrame. Each training example should be JSONL record with two keys, for
    example:
      {
        "input_text": <input prompt>,
        "output_text": <associated output>
      },
    or the pandas DataFame should contain two columns:
      ['input_text', 'output_text']
    with rows for each training example.

    Args:
      model_display_name: Customized Tuned LLM model name.
      training_data: GCS URI of jsonl file or pandas dataframe of training data.
      train_steps: Number of training steps to use when tuning the model.
      evaluation_dataset: GCS URI of jsonl file of evaluation data.
      tensorboard_instance_name: The full name of the existing Vertex AI TensorBoard instance:
        projects/PROJECT_ID/locations/LOCATION_ID/tensorboards/TENSORBOARD_INSTANCE_ID
        Note that this instance must be in the same region as your tuning job.
    """
    vertexai.init(
        project=GCP_PROJECT_ID, location=GCP_LLM_LOCATION, credentials=credentials
    )

    eval_spec = TuningEvaluationSpec(evaluation_data=evaluation_dataset)
    # Removed tensorboard - not sure how to make it work; it provides some extra visualistion during training
    # eval_spec.tensorboard = aiplatform.Tensorboard(tensorboard_name=tensorboard_instance_name)

    model = TextGenerationModel.from_pretrained("text-bison@002")

    model.tune_model(
        training_data=training_data,
        model_display_name=model_display_name,
        train_steps=train_steps,
        tuning_job_location=GCP_TUNED_MODEL_LOCATION,
        tuned_model_location=GCP_TUNED_MODEL_LOCATION,
        tuning_evaluation_spec=eval_spec,
    )
    return model


def prepend_prompt(chunk, prompt):
    """We need to insert the prompt as the start of each input row and
    wrap the text in the prompt in triple-backticks."""
    # TODO: this is now pretty trivial; not sure we need it as a function at all!
    # as done in vertex.generate_reponse() - should probably define this just once...
    return f"{prompt}\n```{chunk}```"


def make_training_set_simple() -> pd.DataFrame:
    """Read a CSV file of labelled data, and create a list-of-JSON
    training set and format as a DataFrame. CSV file should have 3 columns:
    output_text (previously extracted claim), input_text (chunk of transcript), flag (True/False)
    where True means "this should be checked" and False means "this is probably fine.
    No header row should be given."""
    # Target data structure: list of dicts
    # [{"input_text":"prompt1","output_text":"output1"}, {"input_text"...,}, ]

    # Load CSV with claim, source-chunk and a True/False flag
    # We need to group all the claims (+ their flags) for each chunk.
    # Where all the flags for a chunk are "False", that means "no need to check this", so we replace the target output with a suitable message.
    # Where any flag is "True", that means "we need to check this" and the target output is a list of the dodgy previously-extracted claim.
    # If some extract claims are fine but some are not, we only want the not-fine ones to be returned, so we can drop the 'false' claims entirely.

    training_data = pd.read_csv("data/training_set.csv")
    training_data.columns = ["output_text", "input_text", "flag"]
    training_data["flag"] = training_data["flag"].astype("bool")

    training_data_final = []
    grps = training_data.groupby("input_text")
    for input_text, grp in grps:
        bad_rows = grp[grp["flag"] == True]
        if len(bad_rows) > 0:
            this_output = "; ".join((bad_rows["output_text"].values))
        else:
            this_output = "seems legit"
        this_row = {
            "input_text": prepend_prompt(input_text, HEALTH_TRAINING_PROMPT),
            "output_text": this_output,
        }
        training_data_final.append(this_row)

    training_data_final_df = pd.DataFrame(training_data_final)
    return training_data_final_df


def make_training_set_explanation() -> pd.DataFrame:
    """(Replacing true/false flag with one of a set of explanations)
    Read a CSV file of labelled data, and create a list-of-JSON
    training set and format as a DataFrame. CSV file should have 3 columns:
    output_text (previously extracted claim), input_text (chunk of transcript),
    explanation (from fixed list of explanation)
    where True means "this should be checked" and False means "this is probably fine.
    No header row should be given.
    Model will be trained to produce structured output: {"claim": <str>, "explanation: <str>}
    See VALID_EXPLANATIONS.
    """
    # Target data structure: list of dicts
    # [{"input_text":"prompt1","output_text":"output1"}, {"input_text"...,}, ]

    # Load CSV with claim, source-chunk and a True/False flag
    # We need to group all the claims (+ their flags) for each chunk.
    # Where all the flags for a chunk are "False", that means "no need to check this", so we replace the target output with a suitable message.
    # Where any flag is "True", that means "we need to check this" and the target output is a list of the dodgy previously-extracted claim.
    # If some extract claims are fine but some are not, we only want the not-fine ones to be returned, so we can drop the 'false' claims entirely.

    training_data = pd.read_csv("data/training_set_v2.csv")
    training_data.columns = ["output_text", "input_text", "explanation"]
    # training_data["flag"] = training_data["flag"].astype("bool")

    training_data_final = []
    grps = training_data.groupby("input_text")
    for input_text, grp in grps:

        this_input = prepend_prompt(input_text, HEALTH_TRAINING_EXPLAIN_PROMPT)
        for index, row in grp.iterrows():
            assert row["explanation"] in VALID_EXPLANATIONS
        this_output = [
            {"claim": row["output_text"], "explanation": row["explanation"]}
            for index, row in grp.iterrows()
        ]
        this_row = {
            "input_text": this_input,
            "output_text": this_output,
        }
        # Maximum input tokens: 8192
        training_data_final.append(this_row)

    training_data_final_df = pd.DataFrame(training_data_final)
    return training_data_final_df


def list_tuned_models() -> None:
    """List tuned models."""
    # not sure this is helpful - really want to list them by the model_display_name that
    # we provide, but it seems to give a google-generated id number.
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_TUNED_MODEL_LOCATION)
    model = TextGenerationModel.from_pretrained("text-bison@001")
    tuned_model_names = model.list_tuned_model_names()
    print(tuned_model_names)

    return tuned_model_names


def get_model_by_display_name(display_name: str) -> TextGenerationModel:
    """Return the fine-tuned model with a given display_name."""
    # TODO: this reads through ALL the models until it finds one with the matching name.
    # If two models have the same name, it'll return one arbitrarily (not good)
    # Is there a more efficient way of doing this?
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_TUNED_MODEL_LOCATION)
    pretrained_model = TextGenerationModel.from_pretrained("text-bison@002")
    tuned_model_names = pretrained_model.list_tuned_model_names()
    for tuned_model_name in tuned_model_names:
        tuned_model = TextGenerationModel.get_tuned_model(tuned_model_name)
        if tuned_model._endpoint.display_name == display_name:
            return tuned_model
    print(f"Model '{display_name}' not found")


def get_video_responses(model, chunks: list[str]) -> list[dict]:
    """Group a list of captions into chunks and pass to fine-tuned model.
    Display responses."""
    all_responses = []

    for chunk in chunks:
        prompt = f"{HEALTH_TRAINING_EXPLAIN_PROMPT}\n```{chunk}``` "
        # To improve JSON, could maybe append: "Sure, here is the output in JSON:\n\n{{"
        # Set max_output_tokens to be higher than default to make sure the JSON response
        # doesn't get truncated (and so become unreadable)
        parameters = {
            "candidate_count": 1,
            "max_output_tokens": 2048,
            "temperature": 0,
            "top_p": 1,
        }
        response = model.predict(prompt, **parameters)
        for candidate in response.candidates:
            # candidate will be a list of 0 or more claims 'cos that's what the prompt asks for!
            try:
                if len(str(candidate.text)) > 0:
                    # print(candidate.safety_attributes)
                    json_text = candidate.text
                    json_text = tidy_response(json_text)
                    formatted_response = {
                        "response": json.loads(json_text),
                        "chunk": chunk,
                        "safety": candidate.safety_attributes,
                    }
                    all_responses.append(formatted_response)
            except Exception as e:
                print("*** problem handling output? *** ", e)
    return all_responses


def pretty_format_responses(responses):
    """Simple formatted display to console for review"""
    for response in responses:
        print(response["chunk"], "\n")
        if len(response.get("response", [])) == 0:
            print("No claims found in response!")
        else:
            display_checkworthy = []
            display_uncheckworthy = []
            for claim in response.get("response", []):
                if claim["explanation"] in CHECKWORTHY_EXPLANATIONS:
                    # print(f">>> {claim['explanation']:20s} {claim['claim']}")
                    display_checkworthy.append(claim)
                elif claim["explanation"] in UNCHECKWORTHY_EXPLANATIONS:
                    display_uncheckworthy.append(claim)
                else:
                    print(f"Unknown explanation! {claim['explanation']}")
            _ = [
                print(f"+++ {claim['explanation']:20s} {claim['claim']}")
                for claim in display_checkworthy
            ]
            _ = [
                print(f"--- {claim['explanation']:20s} {claim['claim']}")
                for claim in display_uncheckworthy
            ]

        print("=" * 80)


if __name__ == "__main__":
    # TODO: add simple command line options to fine-tune or load/use a model or evaluate
    mode = "infer"

    if mode == "train":
        # Fine-tune a new model:
        # _training_data = make_training_set()
        _training_data = make_training_set_explanation()
        _training_data.to_json("data/train_data_v2.json", orient="records", lines=True)
        tuning("dc_tuned_explain_0", _training_data)

    if mode == "infer":
        model = get_model_by_display_name("dc_tuned_explain_0")

        some_captions = youtube_api.load_texts("heart_disease_nat_rem")
        # some_captions = youtube_api.load_texts("prostate_cancer_nat_rem")

        all_responses = []
        for captions in some_captions[0:3]:
            chunks = youtube_api.form_chunks(captions)
            all_responses += get_video_responses(model, chunks)
        print("\n\n")
        pretty_format_responses(all_responses)
