from pytest import mark, param
from health_misinfo_shared import fine_tuning
from health_misinfo_shared.label_scoring import (
    get_claim_summary,
    calculate_claim_summary_score,
    decide_claim_summary_label,
    LABEL_SCORES,
)


@mark.parametrize(
    "chunk,expected_harm",
    [
        param(
            "It is well known that cucumbers cure cancer if used correctly.",
            "high harm",
        ),
        param(
            "It is well known that cucumbers taste bland even if used correctly.",
            "harmless",
        ),
    ],
)
def test_model_harm(chunk: str, expected_harm: str):
    model = fine_tuning.get_model_by_display_name("dc_tuned_explain_0")

    chunk_dict = {"text": chunk}

    model_output = [
        r["response"][0]
        for r in fine_tuning.get_video_responses(model, [chunk_dict], multilabel=True)
    ]

    assert model_output[0]["labels"]["harm"] == expected_harm


@mark.parametrize(
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


@mark.parametrize(
    "labels, target_scores, total_score",
    [
        (
            {
                "understandability": "understandable",
                "type_of_claim": "hedged claim",
                "type_of_medical_claim": "prevention",
                "support": "novel claim",
                "harm": "low harm",
            },
            {
                "understandability": 1,
                "type_of_claim": -3,
                "type_of_medical_claim": 5,
                "support": 7,
                "harm": 5,
            },
            109,
        )
    ],
)
def test_claim_summary_score(
    labels,
    target_scores,
    total_score,
):
    for feature, label in labels.items():
        assert LABEL_SCORES[feature][label] == target_scores[feature]
    assert calculate_claim_summary_score(labels) == total_score
