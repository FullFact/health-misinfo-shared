import json
import pprint
from typing import Any


def compare_format(
    generated_output: list[dict[str, Any]], expected_output: dict[str, Any]
) -> tuple[bool, str]:
    # fail if the generated output isn't a list of dicts
    if not isinstance(generated_output, list):
        return False, "output is not list"

    # loop through each dictionary and check the keys match
    for claim in generated_output:
        if not isinstance(claim, dict):
            return False, "claims are not all dicts"

        if claim.keys() != expected_output.keys():
            return (
                False,
                f"output claim does not have the expected keys: found {list(claim.keys())}, expected {list(expected_output.keys())}",
            )

        if "labels" not in claim or not isinstance(claim["labels"], dict):
            return False, "labels are not present"

        if claim["labels"].keys() != expected_output["labels"].keys():
            return (
                False,
                f"the labels are incorrect: found {list(claim['labels'].keys())}, expected {list(expected_output['labels'].keys())}",
            )

    return True, "output is correctly formatted"


def get_assert(output: str, context: dict[str, Any]) -> bool | float | dict[str, Any]:
    variables = context["vars"]
    generated_output = json.loads(output)
    expected_output = json.loads(variables["expected_output"])

    # fail if the output claims don't match the expected claims formatting
    formats_match, reason = compare_format(generated_output, expected_output[0])
    return {
        "pass": formats_match,
        "score": 1 if formats_match else 0,
        "reason": reason,
    }


if __name__ == "__main__":
    test_generated_output = """
    [
        {
            "claim": "The sky is blue.",
            "original_text": "As we all know, it is blue",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        },
        {
            "claim": "mushrooms cure cancer",
            "original_text": "mushrooms cure cancer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "high harm",
                    "summary": "worth checking"
                }
        }
    ]
    """.strip()

    test_generated_output_bad_1 = """
    [
        {
            "claim": "The sky is blue.",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        }
    ]
    """.strip()

    test_generated_output_bad_2 = """
    [
        {
            "claim": "The sky is blue.",
            "original_text": "As we all know, it is blue",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless"
                }
        }
    ]
    """.strip()

    test_generated_output_bad_3 = """
    {
        "claim": "The sky is blue.",
        "original_text": "As we all know, it is blue",
        "labels":
            {
                "understandability": "understandable",
                "type_of_claim": "statement of fact",
                "type_of_medical_claim": "not medical",
                "support": "uncontroversial statement",
                "harm": "harmless"
            }
    }
    """.strip()

    test_expected_output = """
    [
        {
            "claim": "The sky is blue.",
            "original_text": "As we all know, it is blue",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        }
    ]
    """.strip()

    output = get_assert(
        test_generated_output,
        context={
            "prompt": "PROMPT",
            "vars": {"expected_output": test_expected_output},
        },
    )
    pprint.pp(output)

    output = get_assert(
        test_generated_output_bad_1,
        context={
            "prompt": "PROMPT",
            "vars": {"expected_output": test_expected_output},
        },
    )
    pprint.pp(output)

    output = get_assert(
        test_generated_output_bad_2,
        context={
            "prompt": "PROMPT",
            "vars": {"expected_output": test_expected_output},
        },
    )
    pprint.pp(output)

    output = get_assert(
        test_generated_output_bad_3,
        context={
            "prompt": "PROMPT",
            "vars": {"expected_output": test_expected_output},
        },
    )
    pprint.pp(output)
