# Code originally from https://cloud.google.com/vertex-ai/docs/generative-ai/models/tune-text-models-supervised?hl=en#generative-ai-tune-model-python_vertex_ai_sdk
# Though had a few issues with it..ascii

from __future__ import annotations
from typing import Optional
from google.auth import default

# from google.cloud import aiplatform
import pandas as pd
import json
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.preview.language_models import TuningEvaluationSpec
from prompts import HEALTH_CLAIM_PROMPT, HEALTH_TRAINING_PROMPT
import youtube_api

credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-east4"  # NB: Gemini is not available in europe-west2 (yet?)
GCP_TUNED_MODEL_LOCATION = "europe-west4"  # where we do fine tuning/model storage


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

    model = TextGenerationModel.from_pretrained("text-bison@001")  # or 002?

    model.tune_model(
        training_data=training_data,
        model_display_name=model_display_name,
        train_steps=train_steps,
        tuning_job_location=GCP_TUNED_MODEL_LOCATION,
        tuned_model_location=GCP_TUNED_MODEL_LOCATION,
        tuning_evaluation_spec=eval_spec,
    )
    return model


def make_training_set() -> pd.DataFrame:
    """Read a CSV file of labelled data, and create a list-of-JSON
    training set and format as a DataFrame"""
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

    def prepend_prompt(chunk):
        """We need to insert the prompt as the start of each input row and
        wrap the text in the prompt in triple-backticks."""
        # as done in vertex.generate_reponse() - should probably define this just once...
        return f"{HEALTH_TRAINING_PROMPT}\n```{chunk}```"

    training_data_final = []
    grps = training_data.groupby("input_text")
    for input_text, grp in grps:
        bad_rows = grp[grp["flag"] == True]
        if len(bad_rows) > 0:
            this_output = "; ".join((bad_rows["output_text"].values))
        else:
            this_output = "seems legit"
        this_row = {
            "input_text": prepend_prompt(input_text),
            "output_text": this_output,
        }
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
    # And is there a more efficient way of doing this?
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_TUNED_MODEL_LOCATION)
    model = TextGenerationModel.from_pretrained("text-bison@001")
    tuned_model_names = model.list_tuned_model_names()
    for tuned_model_name in tuned_model_names:
        tuned_model = TextGenerationModel.get_tuned_model(tuned_model_name)
        if tuned_model._endpoint.display_name == display_name:
            return tuned_model


def get_video_responses(model, chunks: list[str]) -> None:
    """Group a list of captions into chunks and pass to fine-tuned model.
    Display responses."""
    all_responses = []

    for chunk in chunks:
        print()
        print(chunk)
        prompt = f"{HEALTH_TRAINING_PROMPT}\n```{chunk}``` "
        # To improve JSON, could append: "Sure, here is the output in JSON:\n\n{{"
        response = model.predict(prompt)
        print("Candidates:\t", response.candidates, "\n")
        for candidate in response.candidates:
            # candidate will be a list of 0 or more claims 'cos that's what the prompt asks for!
            try:
                if len(str(candidate.text)) > 0:
                    print(candidate.safety_attributes)
                    json_text = candidate.text
                    print("JSON output:  ", json_text)
                    formatted_response = {
                        "claim": json.loads(candidate.text),
                        "chunk": chunk,
                        "safety": candidate.safety_attributes,
                    }
                    all_responses.append(formatted_response)
            except Exception as e:
                print("*** problem handling output? *** ", e)
        print("=" * 80)
    return all_responses


if __name__ == "__main__":
    # Fine-tune a new model:
    # _training_data = make_training_set()
    # tuning("dc_tuned_2", _training_data)

    # tuned_model_names = list_tuned_models()
    # Awkward way of reloading model - works if you know the id
    # model id 1304095557333024768 is dc_tuned_2
    # model = TextGenerationModel.get_tuned_model(model_id)

    model = get_model_by_display_name("dc_tuned_2")

    some_captions = youtube_api.load_texts("heart_disease_nat_rem")
    # chunks = youtube_api.form_chunks(some_captions[1])

    all_responses = []
    for captions in some_captions[0:5]:
        chunks = youtube_api.form_chunks(captions)
        all_responses += get_video_responses(model, chunks)
    print("\n\n")
    print(all_responses)
