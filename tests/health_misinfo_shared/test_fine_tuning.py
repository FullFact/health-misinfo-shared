import pandas as pd
from health_misinfo_shared import fine_tuning, evaluation, prompts
from health_misinfo_shared.label_scoring import (
    get_claim_summary,
    calculate_claim_summary_score,
    decide_claim_summary_label,
    LABEL_SCORES,
)
import pytest


def test_eval():

    model = fine_tuning.get_model_by_display_name("dc_tuned_explain_0")

    target_data = pd.DataFrame.from_records(
        data=[
            [
                "Cucumbers can cure cancer",
                "It is well known that cucumbers cure cancer if used correctly.",
                "high harm",
            ],
            [
                "Cucumbers can taste bland",
                "It is well known that cucumbers taste bland even if used correctly.",
                "nothing to check",
            ],
        ],
        columns=["claim", "chunk", "explanation"],
    )

    raw_results = evaluation.explain_build_results_table(model, target_data)
    metrics_results = evaluation.evaluate(raw_results)

    assert metrics_results["precision"] == 1.0
    assert metrics_results["recall"] == 1.0


@pytest.mark.parametrize(
    "score, summary",
    [
        (-100, "not worth checking"),
        (0, "not worth checking"),
        (99, "not worth checking"),
        (100, "not worth checking"),
        (101, "may be worth checking"),
        (199, "may be worth checking"),
        (200, "may be worth checking"),
        (201, "worth checking"),
        (float("inf"), "worth checking"),
    ],
)
def test_decide_claim_summary_label(score, summary):
    assert decide_claim_summary_label(score) == summary


@pytest.mark.parametrize(
    "labels, score",
    [
        (
            {
                "understandability": "understandable",
                "type_of_claim": "hedged claim",
                "type_of_medical_claim": "prevention",
                "support": "novel claim",
                "harm": "low harm",
            },
            1,
            -3,
            5,
            7,
            5,
            100,
        )
    ],
)
def test_claim_summary_score(
    labels,
    und_score,
    type_claim_score,
    med_type_score,
    support_score,
    harm_score,
    total_score,
):
    assert calculate_claim_summary_score(labels) == total_score
