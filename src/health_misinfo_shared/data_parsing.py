import re
import ast
import json
from typing import Any


def parse_json_string(json_string: str) -> dict[str, Any] | None:
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(json_string)
        except Exception as e:
            return None


def parse_model_json_output(model_output: str) -> list[dict[str, str]]:
    original_output = model_output
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
    except Exception as e:
        pass
    raise Exception("Could not parse the string: ", model_output, original_output)
