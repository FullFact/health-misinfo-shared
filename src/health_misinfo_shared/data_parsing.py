import ast
import json
from typing import Any


def tidy_response(response_text: str) -> str:
    """Strip unnecessary head/tail of response string"""
    # TODO: Maybe investigate this library instead: https://github.com/noamgat/lm-format-enforcer
    response_text = response_text.strip(" `'\".")
    if response_text.startswith("json"):
        response_text = response_text[5:]
    return response_text


def parse_json_string(json_string: str) -> dict[str, Any] | None:
    try:
        return json.loads(json_string, strict=False)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(json_string)
        except Exception:
            return None


def parse_model_json_output(model_output: str) -> list[dict[str, str]]:
    original_output = model_output
    model_output = tidy_response(model_output)
    model_output = model_output.strip()
    # model_output = re.sub(r"```", "", model_output.strip()).rstrip("\n").lstrip("json")
    try:
        if model_output.startswith("[") and model_output.endswith("]"):
            return parse_json_string(model_output)

        first_square_bracket_idx = model_output.find("[")
        last_square_bracket_idx = model_output.rfind("]")
        if first_square_bracket_idx >= 0 and last_square_bracket_idx >= 0:
            return parse_json_string(
                model_output[first_square_bracket_idx : last_square_bracket_idx + 1]
            )
    except Exception:
        pass
    raise Exception("Could not parse the string: ", model_output, original_output)
