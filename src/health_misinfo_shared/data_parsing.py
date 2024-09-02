from typing import cast

import json_repair


def parse_model_json_output(model_output: str) -> list[dict[str, str]]:
    if not (parsed := json_repair.loads(model_output)):
        raise Exception("Could not parse the string: ", model_output)
    return cast(list[dict[str, str]], parsed)
