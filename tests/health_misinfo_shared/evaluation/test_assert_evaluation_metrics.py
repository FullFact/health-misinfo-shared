from pytest import mark, param
from typing import Any
from evaluation.assert_evaluation_metrics import get_eval_metrics


DEFAULT_EXPECTED_OUTPUT = [
    {
        "claim": "The sky is blue.",
        "original_text": "As we all know, it is blue",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "not medical",
            "support": "uncontroversial statement",
            "harm": "harmless",
            "summary": "not worth checking",
        },
    },
    {
        "claim": "mushrooms cure cancer",
        "original_text": "mushrooms cure cancer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "high harm",
            "summary": "worth checking",
        },
    },
    {
        "claim": "The writer has a dog called Geoff",
        "original_text": "I have a dog called Geoff",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "not medical",
            "support": "uncontroversial statement",
            "harm": "harmless",
            "summary": "not worth checking",
        },
    },
    {
        "claim": "Eating walnuts will make you live longer",
        "original_text": "Eating walnuts will make you live longer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "low harm",
            "summary": "may be worth checking",
        },
    },
]

OTHER_CLAIMS = [
    {
        "claim": "Mud is good for human digestion.",
        "original_text": "Mud is good for your tummy.",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "not medical",
            "support": "uncontroversial statement",
            "harm": "harmless",
            "summary": "worth checking",
        },
    },
    {
        "claim": "Eels are wriggly.",
        "original_text": "They are wriggly",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "low harm",
            "summary": "may be worth checking",
        },
    },
    {
        "claim": "Eating walnuts might make you live longer",
        "original_text": "Eating walnuts will make you live longer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "low harm",
            "summary": "may be worth checking",
        },
    },
    {
        "claim": "Eating walnuts may extend your life",
        "original_text": "Eating walnuts might make you live longer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "low harm",
            "summary": "may be worth checking",
        },
    },
    {
        "claim": "mushrooms cure cancer",
        "original_text": "mushrooms cure cancer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "high harm",
            "summary": "may be worth checking",
        },
    },
    {
        "claim": "mushrooms cure cancer",
        "original_text": "mushrooms cure cancer",
        "labels": {
            "understandability": "understandable",
            "type_of_claim": "statement of fact",
            "type_of_medical_claim": "cause/effect",
            "support": "novel claim",
            "harm": "high harm",
            "summary": "not worth checking",
        },
    },
]


@mark.parametrize(
    "generated_output, expected_output, expected_metrics",
    [
        param(
            DEFAULT_EXPECTED_OUTPUT,
            DEFAULT_EXPECTED_OUTPUT,
            {"precision": 1.0, "recall": 1.0, "f1": 1.0},
            id="Exact match",
        ),
        param(
            DEFAULT_EXPECTED_OUTPUT[1:],
            DEFAULT_EXPECTED_OUTPUT,
            # this is the correct output but behaviour is questionable
            {"f1": 1.0, "precision": 1.0, "recall": 1.0},
            id="Output missing 1 claim",
        ),
        param(
            DEFAULT_EXPECTED_OUTPUT,
            DEFAULT_EXPECTED_OUTPUT[:-1],
            # this is the correct output but behaviour is questionable
            {"f1": 2 / 3, "precision": 0.5, "recall": 1.0},
            id="Extra claims in output",
        ),
        param(
            OTHER_CLAIMS[:2],
            DEFAULT_EXPECTED_OUTPUT,
            {"precision": 0, "recall": 0, "f1": 0},
            id="No matching claims",
        ),
        param(
            [],
            DEFAULT_EXPECTED_OUTPUT,
            {"precision": 0, "recall": 0, "f1": 0},
            id="No output claims at all",
        ),
        param(
            DEFAULT_EXPECTED_OUTPUT,
            [],
            {"precision": 0, "recall": 0, "f1": 0},
            id="No expected claims",
        ),
        param(
            [],
            [],
            {"precision": 1.0, "recall": 1.0, "f1": 1.0},
            id="None of either",
        ),
        param(
            [OTHER_CLAIMS[2]],
            [DEFAULT_EXPECTED_OUTPUT[3]],
            {"precision": 1.0, "recall": 1.0, "f1": 1.0},
            id="Wording of claim slightly different.",
        ),
        param(
            [OTHER_CLAIMS[3]],
            [DEFAULT_EXPECTED_OUTPUT[3]],
            {"precision": 0, "recall": 0, "f1": 0},
            id="Wording of claim very different",
        ),
        param(
            [OTHER_CLAIMS[4]],
            [DEFAULT_EXPECTED_OUTPUT[1]],
            {"precision": 1.0, "recall": 1.0, "f1": 1.0},
            id="output has different but still checkworthy label",
        ),
        param(
            [OTHER_CLAIMS[5]],
            [DEFAULT_EXPECTED_OUTPUT[1]],
            {"precision": 0, "recall": 0, "f1": 0},
            id="output has different and uncheckworthy label",
        ),
    ],
)
def test_get_eval_metrics(
    generated_output: list[dict[str, Any]],
    expected_output: list[dict[str, Any]],
    expected_metrics: dict[str, Any],
):
    metrics = get_eval_metrics(generated_output, expected_output)
    assert metrics == expected_metrics
