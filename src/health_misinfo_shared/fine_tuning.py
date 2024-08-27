# Code originally from https://cloud.google.com/vertex-ai/docs/generative-ai/models/tune-text-models-supervised?hl=en#generative-ai-tune-model-python_vertex_ai_sdk
# Though had a few issues with it..ascii

import json
from typing import Any, Iterable
from pathlib import Path
import json
import pandas as pd
from google.auth import default
import vertexai
from vertexai.language_models import TextGenerationModel
from vertexai.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
from vertexai.preview.language_models import TuningEvaluationSpec

from health_misinfo_shared.prompts import (
    HEALTH_TRAINING_PROMPT,
    HEALTH_TRAINING_EXPLAIN_PROMPT,
    HEALTH_TRAINING_MULTI_LABEL_PROMPT,
    HEALTH_INFER_MULTI_LABEL_PROMPT,
    MULTIMODAL_RAPHAEL_PROMPT,
)
from health_misinfo_shared import youtube_api
from health_misinfo_shared.data_parsing import parse_model_json_output
from health_misinfo_shared.label_scoring import get_claim_summary
from health_misinfo_shared.claim_format_checker import (
    StrictClaimModel,
    ClaimModel,
)


GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-central1"  # NB: Gemini is not available in europe-west2 (yet?)
GCP_TUNED_MODEL_LOCATION = "europe-west4"  # where we do fine tuning/model storage
CHECKWORTHY_EXPLANATIONS = ["high harm", "citation", "low harm"]
UNCHECKWORTHY_EXPLANATIONS = ["nothing to check", "hedged claim"]
VALID_EXPLANATIONS = CHECKWORTHY_EXPLANATIONS + UNCHECKWORTHY_EXPLANATIONS

VIDEO_SAFETY_SETTINGS = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}


def tuning(
    model_display_name: str,
    training_data: pd.DataFrame | str,
    train_steps: int = 10,
    evaluation_dataset: str | None = None,
    tensorboard_instance_name: str | None = None,
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
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
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


def make_training_set_multi_label(
    annotated_files: list[str], include_prompt=True
) -> pd.DataFrame:
    """
    Same as function above, but uses multi label training data.
    This will fail if labelled data is not multi-label, using the labels below.
    Reads list of CSV files and merges into a dataframe.
    If include_prompt is True, then prepend an appropriate prompt to the input text.
    Set to false for in-context learning, where we don't want to repeat the prompt with every example.
    """
    # training_data = pd.read_csv("data/multi_label_training_v1.csv")

    training_data_final = []
    for fn in annotated_files:
        training_data = pd.read_csv(fn)
        if "summary" in training_data.columns:
            training_data = training_data.drop(columns="summary")
        training_data.columns = [
            "output_text",
            "input_text",
            "understandability",
            "type_of_claim",
            "type_of_medical_claim",
            "support",
            "harm",
        ]
        grps = training_data.groupby("input_text")

        for input_text, grp in grps:
            if include_prompt:
                this_input = prepend_prompt(
                    input_text, HEALTH_TRAINING_MULTI_LABEL_PROMPT
                )
            else:
                this_input = input_text
            # for index, row in grp.iterrows():
            #     assert row["explanation"] in VALID_EXPLANATIONS
            this_output = [
                {
                    "claim": row["output_text"],
                    "labels": {
                        "understandability": row.get("understandability", "vague"),
                        "type_of_claim": row.get("type_of_claim", "not a claim"),
                        "type_of_medical_claim": row.get(
                            "type_of_medical_claim", "not medical"
                        ),
                        "support": row.get("support", "can't tell"),
                        "harm": row.get("harm", "can't tell"),
                    },
                }
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


def get_video_responses(
    model,
    chunks: Iterable[dict[str, Any]],
    multilabel: bool = False,
    in_context_examples: str = "",
) -> Iterable[dict[str, Any]]:
    """Group a list of captions into chunks and pass to fine-tuned model.
    Display responses."""
    infer_prompt = (
        HEALTH_INFER_MULTI_LABEL_PROMPT
        if multilabel
        else HEALTH_TRAINING_EXPLAIN_PROMPT
    )
    if len(in_context_examples) > 0:
        infer_prompt += (
            "\nHere are some examples to learn from:\n" + in_context_examples
        )

    for chunk in chunks:
        if isinstance(chunk, str):
            # for fine-tuning
            chunk_text = chunk
        elif isinstance(chunk, dict):
            # for app
            chunk_text = chunk["text"]
        prompt = f"{infer_prompt}\n```{chunk_text}```"
        # To improve JSON, could append: "Sure, here is the output in JSON:\n\n{{"
        # Set max_output_tokens to be higher than default to make sure the JSON response
        # doesn't get truncated (and so become unreadable)
        parameters = {
            "candidate_count": 1,
            "max_output_tokens": 2048,
            "temperature": 0,
            "top_p": 1,
        }

        attempts = 3
        for _ in range(attempts):
            if in_context_examples:
                response = model.generate_content(
                    [prompt],
                    generation_config=parameters,
                    safety_settings=VIDEO_SAFETY_SETTINGS,
                )
            else:
                response = model.predict(
                    prompt, **parameters, safety_settings=VIDEO_SAFETY_SETTINGS
                )
            candidate = response.candidates[0]
            try:
                claims = parse_model_json_output(candidate.text)
                [StrictClaimModel(**c) for c in claims]
                break
            except Exception as e:
                print("*** problem handling output? *** ", e)
        else:
            claims = [ClaimModel(**c).model_dump() for c in claims]

        # claims will be a list of 0 or more claims 'cos that's what the prompt asks for!
        # print(candidate.safety_attributes)
        formatted_response = {
            "response": claims,
            "chunk": chunk,
            # "safety": candidate.safety_attributes,
        }
        yield formatted_response


def pretty_format_responses(responses, multilabel: bool = False):
    """Simple formatted display to console for review"""

    for response in responses:
        print(response["chunk"], "\n")
        if len(response.get("response", [])) == 0:
            print("No claims found!")
        else:
            for claim in response.get("response", []):
                if multilabel:
                    print(f">>> {claim['claim']}")
                    print(f"    {claim['labels']}")
                    print(f"    Summary: {get_claim_summary(claim['labels'])}")
                else:
                    print(f">>> {claim['explanation']:20s} {claim['claim']}")
        print("=" * 80)


def save_all_responses(
    responses, texts_name, multilabel: bool = False, folder: str = "labels"
) -> None:
    """
    Export responses to a csv. Format depends on if a multilabel response or not.
    """
    # TODO: check directory exists (& create it) before writing
    claims, chunks = [], []
    if multilabel:
        understandable, type_of_claim, med_type = [], [], []
        support, harm, summary = [], [], []
    else:
        explanations = []

    for response in responses:
        # if len(response.get("claim", [])) > 0:
        for claim in response.get("response", []):
            claims.append(claim.get("claim"))
            chunks.append(response.get("chunk"))
            if multilabel:
                labels = claim.get("labels")
                understandable.append(labels.get("understandability"))
                type_of_claim.append(labels.get("type_of_claim"))
                med_type.append(labels.get("type_of_medical_claim"))
                support.append(labels.get("support"))
                harm.append(labels.get("harm"))
                summary.append(get_claim_summary(labels))
            else:
                explanations.append(claim.get("explanation"))
    if multilabel:
        data = pd.DataFrame(
            {
                "chunk": chunks,
                "claim": claims,
                "understandability": understandable,
                "type of claim": type_of_claim,
                "medical claim type": med_type,
                "support": support,
                "harm": harm,
                "summary": summary,
            }
        )
        datapath = f"data/inferred_labels/{folder}/{texts_name}_labels.csv"
    else:
        data = pd.DataFrame(
            {
                "chunk": chunks,
                "claim": claims,
                "explanation": explanations,
            }
        )
        datapath = f"data/inferred_labels/{texts_name}_labels.csv"
    data.to_csv(datapath, index=False)


def construct_in_context_examples(
    data_filenames: list[str], split_frac=0.9
) -> tuple[str, list[dict]]:
    """
    Read annotated data from a list of files. Use some of that to build a single prompt
    (for in-context learning). Return the rest of the data as a list of labelled examples,
    ready for use as evaluation data.
    split_frac specifies what fraction to hold back for evaluation. Set to 1.0 means use all
    available data in the prompt.
    """

    _training_data = make_training_set_multi_label(data_filenames, include_prompt=False)
    _training_data = _training_data.sample(frac=1)  # shuffle rows

    examples = ""
    split_position = int(_training_data.shape[0] * split_frac)
    hold_out_set = _training_data.iloc[split_position:, :]

    for _id, eg in _training_data.head(split_position).iterrows():
        examples += f"Input: {eg['input_text']}\n"
        target = eg["output_text"]
        for t in target:
            # summary should be one of "not worth checking", "worth checking", "may be worth checking"
            # TODO: improve logic here. E.g. use an internal score, so 'citation' adds 1, 'high harm' adds 2, 'low harm' adds 1 etc.
            # then map back to label

            t["labels"]["summary"] = get_claim_summary(t["labels"])

        examples += f"Output: {json.dumps(target)}\n"
    return examples, hold_out_set


def infer_transcript_claims(transcript: list[dict]) -> Iterable[dict[str, Any]]:
    """For use in app"""
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_TUNED_MODEL_LOCATION)

    chunks = youtube_api.form_chunks(transcript)
    model = GenerativeModel("gemini-1.5-pro-preview-0514")
    annotated_data_files = [
        (Path(__file__).parent / "full_in_context_labelled_data.csv")
    ]
    in_context_examples, empty_hold_out_set = construct_in_context_examples(
        annotated_data_files, split_frac=1.0
    )
    # print(in_context_examples)
    all_responses = get_video_responses(
        model, chunks, multilabel=True, in_context_examples=in_context_examples
    )

    return all_responses


def infer_multimodal_claims(
    bucket_name: str, video_path: str, model_name: str = "gemini-1.5-flash-001"
) -> Iterable[dict[str, Any]]:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LLM_LOCATION)
    model = GenerativeModel(model_name=model_name)
    print("FINE TUNING", video_path)
    response = model.generate_content(
        [
            Part.from_uri("gs://" + video_path, mime_type="video/mp4"),
            MULTIMODAL_RAPHAEL_PROMPT,
        ],
        safety_settings=VIDEO_SAFETY_SETTINGS,
        generation_config={
            "candidate_count": 1,
            "max_output_tokens": 8192,
            "temperature": 0,
            "top_p": 1,
        },
    )

    if not len(response.candidates):
        raise Exception(f"No model output: possible reason: {response.prompt_feedback}")

    candidate = response.candidates[0]
    text = candidate.text
    if text.startswith("```"):
        text = text.strip("`")
    if text.startswith("json"):
        text = text[4:]
    print(text)
    return json.loads(text)


if __name__ == "__main__":
    # TODO: add simple command line options to fine-tune or load/use a model or evaluate
    mode = "in_context"

    texts_list = [
        "acne_nat_rem",
        "ADHD_nat_rem",
        "heart_disease_nat_rem",
        "HPV_nat_rem",
        "prostate_cancer_nat_rem",
        "std_nat_rem",
        "weight_loss_nat_rem",
    ]

    # Set to False is not the multilabel training set.
    multilabel = True

    if mode == "train":
        # Fine-tune a new model:
        # _training_data = make_training_set()
        _training_data = make_training_set_multi_label(
            ["data/multi_label_training_v1.csv"]
        )
        _training_data.to_json(
            "data/multi_label_training_v1.json", orient="records", lines=True
        )
        tuning("cj_tuned_multi_label_0", _training_data)

    if mode == "in_context":
        model = GenerativeModel(
            "gemini-1.5-pro-preview-0514"
        )  # or is it 0514 (May 15th update)
        annotated_data_files = [
            (Path(__file__).parent / "full_in_context_labelled_data.csv")
        ]
        examples, eval_set = construct_in_context_examples(annotated_data_files)
        # for texts in texts_list[0:4]:
        #     some_captions = youtube_api.load_texts(texts)

        #     all_responses = []
        #     for captions in some_captions[0:5]:
        #         chunks = youtube_api.form_chunks(captions)
        eval_chunk = []
        for idx, eval_row in eval_set.iterrows():
            eval_chunk.append(eval_row["input_text"])

        print("\n\nEval chunk:\n", eval_chunk)
        all_responses = list(
            get_video_responses(
                model, eval_chunk, multilabel, in_context_examples=examples
            )
        )
        print("\n\n")
        pretty_format_responses(all_responses, multilabel)
        save_all_responses(all_responses, "hold_out", multilabel, folder="ICL")

    if mode == "infer":
        model = get_model_by_display_name("cj_tuned_multi_label_0")

        # some_captions = youtube_api.load_texts("heart_disease_nat_rem")
        # # some_captions = youtube_api.load_texts("prostate_cancer_nat_rem")

        # all_responses = []
        # for captions in some_captions[0:3]:
        #     chunks = youtube_api.form_chunks(captions)
        #     all_responses += get_video_responses(model, chunks)
        # print("\n\n")
        # pretty_format_responses(all_responses)

        for texts in texts_list[0:2]:
            some_captions = youtube_api.load_texts(texts)

            all_responses = []
            for captions in some_captions[0:5]:
                chunks = youtube_api.form_chunks(captions)
                all_responses += list(get_video_responses(model, chunks, multilabel))
            print("\n\n")
            # save_all_responses(all_responses, texts, multilabel)
            pretty_format_responses(all_responses, multilabel)
