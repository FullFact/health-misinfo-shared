import os
import pandas as pd
from google.cloud import aiplatform

from google.auth import default


credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_PROJECT_NUMBER = 1447178727
GCP_LLM_LOCATION = "europe-west4"  # NB: Gemini is not available in europe-west2 (yet?)
CURRENT_MODEL = "gemini-1.0-pro"

BUCKET_FOLDER = "gs://fullfact-raphael-eval"
EVALUATION_DATASET = os.path.join(BUCKET_FOLDER, "autosxs_eval.jsonl")

RUN_NAME = "autosxs-template-20240520143552"


def run_autosxs():
    prompt_column = "text"
    parameters = {
        "evaluation_dataset": EVALUATION_DATASET,
        "id_columns": [prompt_column],
        "task": "summarization",
        "autorater_prompt_parameters": {
            "inference_context": {"column": prompt_column},
            "inference_instruction": {
                "template": "Find all health claims in the following, returning your answer as a json list only: {{"
                + prompt_column
                + "}}"
            },
        },
        "model_a": "publishers/google/models/text-bison@001",
        "model_a_prompt_parameters": {
            "prompt": {
                "template": "Find all health claims in the following, returning your answer as a json list only: {{"
                + prompt_column
                + "}}.",
            },
        },
        "response_column_b": "claims",
    }
    aiplatform.init(
        project=GCP_PROJECT_ID,
        location=GCP_LLM_LOCATION,
        staging_bucket=BUCKET_FOLDER,
    )
    display_name = "autosxs_ed_test"
    job = aiplatform.PipelineJob(
        display_name=display_name,
        pipeline_root=os.path.join(BUCKET_FOLDER, display_name),
        template_path=(
            "https://us-kfp.pkg.dev/ml-pipeline/google-cloud-registry/autosxs-template/default"
        ),
        parameter_values=parameters,
    )
    job.run()
    parse_results(job=job)


def parse_results(job=None):
    run_name = RUN_NAME if job is None else job.job_id

    if job is None:
        job = aiplatform.PipelineJob.get(
            f"projects/{GCP_PROJECT_NUMBER}/locations/{GCP_LLM_LOCATION}/pipelineJobs/{run_name}"
        )

    # make a directory for the results
    directory = os.path.join("dev/prompt_evaluation", run_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for details in job.task_details:
        if details.task_name == "online-evaluation-pairwise":
            break

    # Judgments
    judgments_uri = details.outputs["judgments"].artifacts[0].uri
    judgments_df = pd.read_json(judgments_uri, lines=True)
    judgments_df.to_csv(os.path.join(directory, "judgments_df.csv"), index=False)

    for details in job.task_details:
        if details.task_name == "online-evaluation-pairwise":
            break

    # Error table
    error_messages_uri = details.outputs["error_messages"].artifacts[0].uri
    errors_df = pd.read_json(error_messages_uri, lines=True)
    errors_df.to_csv(os.path.join(directory, "errors_df.csv"), index=False)

    # Metrics
    for details in job.task_details:
        if details.task_name == "model-evaluation-text-generation-pairwise":
            break
    metrics_df = pd.DataFrame(
        [details.outputs["autosxs_metrics"].artifacts[0].metadata]
    )
    metrics_df.to_csv(os.path.join(directory, "metrics_df.csv"), index=False)


if __name__ == "__main__":
    run_autosxs()
    # parse_results()
