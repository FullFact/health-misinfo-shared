import re
import ast
import json


def parse_model_json_output(model_output: str) -> list[dict[str, str]]:
    original_output = model_output
    model_output = re.sub(r"```", "", model_output.strip()).rstrip("\n").lstrip("json")
    if model_output.startswith("[") and model_output.endswith("]"):
        return json.loads(ast.literal_eval(model_output))

    first_square_bracket_idx = model_output.find("[")
    last_square_bracket_idx = model_output.rfind("]")
    if first_square_bracket_idx > 0 and last_square_bracket_idx > 0:
        return json.loads(
            ast.literal_eval(
                model_output[first_square_bracket_idx : last_square_bracket_idx + 1]
            )
        )
    raise Exception("Could not parse the string: ", model_output, original_output)
