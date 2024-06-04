from pytest import mark, param
from typing import Any
from evaluation.assert_check_format import compare_format


EXAMPLE_CLAIM = {
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
}


@mark.parametrize(
    "generated_output,example_claim,expected_pass",
    [
        param(
            [
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
            ],
            EXAMPLE_CLAIM,
            True,
            id="Normal match",
        ),
        param(
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
            EXAMPLE_CLAIM,
            False,
            id="Output isn't a list",
        ),
        param(
            ["claim 1", "claim 2"],
            EXAMPLE_CLAIM,
            False,
            id="Output is a list of strings (not dicts)",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                    "not_labels": {
                        "understandability": "understandable",
                        "type_of_claim": "statement of fact",
                        "type_of_medical_claim": "cause/effect",
                        "support": "novel claim",
                        "harm": "high harm",
                        "summary": "worth checking",
                    },
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="Claim keys don't match",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="Labels not in output claims",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                    "labels": [
                        "understandable",
                        "statement of fact",
                        "cause/effect",
                        "novel claim",
                        "high harm",
                        "worth checking",
                    ],
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="labels is not a dictionary",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                    "labels": {
                        "understandability": "understandable",
                        "type_of_claim": "statement of fact",
                        "type_of_medical_claim": "cause/effect",
                        "support": "novel claim",
                        "harm": "high harm",
                        "conclusion": "worth checking",
                    },
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="label keys don't match",
        ),
        param(
            [
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
                        "conclusion": "fake news!",
                    },
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="Too many labels in output",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                    "labels": {
                        "understandability": "understandable",
                        "type_of_claim": "statement of fact",
                        "type_of_medical_claim": "cause/effect",
                        "support": "novel claim",
                        "harm": "high harm",
                    },
                },
            ],
            EXAMPLE_CLAIM,
            False,
            id="too few labels in output",
        ),
        param(
            [
                {
                    "claim": "mushrooms cure cancer",
                    "original_text": "mushrooms cure cancer",
                    "labels": {
                        "understandability": 1,
                        "type_of_claim": 1,
                        "type_of_medical_claim": 1,
                        "support": 1,
                        "harm": 1,
                        "summary": 1,
                    },
                },
            ],
            EXAMPLE_CLAIM,
            True,
            id="type mismatch in labels",
        ),
    ],
)
def test_compare_format(
    generated_output: list[dict[str, Any]],
    example_claim: dict[str, Any],
    expected_pass: bool,
):
    does_pass, reason = compare_format(
        generated_output=generated_output, expected_output=example_claim
    )
    assert does_pass == expected_pass
