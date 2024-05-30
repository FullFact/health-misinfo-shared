import re
import json
from typing import Any
from pprint import pformat, pp


def check_quote_in_chunk(quote: str, chunk: str) -> bool:
    not_alphanum_pattern = re.compile(r"[^a-zA-Z0-9 ]")
    stripped_quote = not_alphanum_pattern.sub("", quote).strip().lower()
    stripped_chunk = not_alphanum_pattern.sub("", chunk).strip().lower()
    return stripped_quote in stripped_chunk


def make_reason(
    claims: list[dict[str, Any]], passes_list: list[bool], chunk: str
) -> str:
    quotes_not_contained = [
        claim["original_text"]
        for claim, does_pass in zip(claims, passes_list)
        if not does_pass
    ]

    return f"""
    The following quotes:
    {pformat(quotes_not_contained)}
    Are not contained in the chunk:
    {chunk}
    """


def get_assert(output: str, context: dict[str, Any]) -> bool | float | dict[str, Any]:
    variables = context["vars"]

    generated_output = json.loads(output)

    quote_in_chunk = [
        check_quote_in_chunk(claim["original_text"], variables["chunk"])
        for claim in generated_output
    ]

    score = sum(quote_in_chunk) / len(quote_in_chunk)
    passes = all(quote_in_chunk)

    # This return is an example GradingResult dict
    return {
        "pass": passes,
        "score": score,
        "reason": (
            "Quotes are all contained in chunk"
            if passes
            else make_reason(generated_output, quote_in_chunk, variables["chunk"])
        ),
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
            "claim": "Eating walnuts will make you live longer",
            "original_text": "Eating walnuts will make you live longer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "low harm",
                    "summary": "may be worth checking"
                }
        }
    ]
    """.strip()

    positive_test_chunk = "We all love the sky. And as we all know, it is blue. Eating walnuts will make you live longer."
    negative_test_chunk = "This has none of those claims"

    output = get_assert(
        test_generated_output,
        context={
            "prompt": "PROMPT",
            "vars": {"chunk": positive_test_chunk},
        },
    )
    pp(output)
    print()
    output = get_assert(
        test_generated_output,
        context={
            "prompt": "PROMPT",
            "vars": {"chunk": negative_test_chunk},
        },
    )
    pp(output)
