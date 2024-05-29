from typing import Any


def get_assert(output: str, context: dict[str, Any]) -> bool | float | dict[str, Any]:
    prompt = context["prompt"]
    variables = context["vars"]

    # This return is an example GradingResult dict
    return {
        "pass": True,
        "score": 0.9,
        "reason": "Quotes are all contained in chunk (test)",
    }
