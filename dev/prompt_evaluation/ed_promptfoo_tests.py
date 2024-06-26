import json
from typing import Any
from dataclasses import dataclass

import vertexai
from vertexai.generative_models import GenerativeModel


GCP_PROJECT_ID = "exemplary-cycle-195718"
GCP_LLM_LOCATION = "us-east1"  # NB: Gemini is not available in europe-west2 (yet?)
CURRENT_MODEL = "gemini-1.0-pro"


class ProcessingException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ParsingException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass(frozen=True)
class ProviderOptions:
    id: str | None
    config: dict[str, Any] | None

    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> "ProviderOptions":
        return ProviderOptions(
            id=dictionary.get("id", None),
            config=dictionary.get("config", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "config": self.config}


@dataclass(frozen=True)
class CallApiContextParams:
    vars: dict[str, str]

    @staticmethod
    def from_dict(dictionary: dict[str, Any]) -> "CallApiContextParams":
        return CallApiContextParams(vars=dictionary["vars"])

    def to_dict(self) -> dict[str, Any]:
        return {"vars": self.vars}


@dataclass(frozen=True)
class TokenUsage:
    total: int
    prompt: int
    completion: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "prompt": self.prompt,
            "completion": self.completion,
        }


@dataclass(frozen=True)
class ProviderResponse:
    output: str | dict[str, Any] | None = None
    error: str | None = None
    tokenUsage: TokenUsage | None = None
    cost: float | None = None
    cached: bool | None = None
    logProbs: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "error": self.error,
            "tokenUsage": (
                self.tokenUsage.to_dict() if self.tokenUsage is not None else None
            ),
            "cost": self.cost,
            "cached": self.cached,
            "logProbs": self.logProbs,
        }


def load_model() -> GenerativeModel:
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_LLM_LOCATION)
    return GenerativeModel(model_name=CURRENT_MODEL)


def parse_model_json_output(model_output: str) -> list[dict[str, str]]:
    model_output = model_output.strip()
    if model_output.startswith("[") and model_output.endswith("]"):
        return json.loads(model_output)

    first_square_bracket_idx = model_output.find("[")
    last_square_bracket_idx = model_output.rfind("]")
    if first_square_bracket_idx > 0 and last_square_bracket_idx > 0:
        return json.loads(
            model_output[first_square_bracket_idx : last_square_bracket_idx + 1]
        )
    raise Exception("Could not parse the string.")


def run_prompt(model: GenerativeModel, prompt: str) -> str:
    parameters = {
        "candidate_count": 1,
        "max_output_tokens": 8192,
        "temperature": 0,
        "top_p": 1,
    }
    try:
        response = model.generate_content(prompt, generation_config=parameters)
    except Exception as e:
        raise ProcessingException(
            f"Error while running prompt. Original error: {repr(e)}"
        )

    try:
        candidate = response.candidates[0]
        return candidate.text
    except Exception as e:
        raise ParsingException(
            f"Could not handle output. It is not in correct json format. Original error: {repr(e)}"
        )


def call_api(
    prompt: str, options: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    parsed_options: ProviderOptions = ProviderOptions.from_dict(options)
    parsed_context: CallApiContextParams = CallApiContextParams.from_dict(context)

    config: dict[str, Any] = parsed_options.config
    additional_option: dict[str, Any] = config.get("additionalOption", None)

    persona = parsed_context.vars.get("persona", None)
    text = parsed_context.vars.get("text", None)
    print(f"Prompt: {prompt[:500]}", end="\n\n")
    print(f"Persona: {persona}\nText Preview: {text[:500]}")

    model: GenerativeModel = load_model()
    print("Loaded model")

    try:
        output: str = run_prompt(model, prompt)
        response = ProviderResponse(output=output, error=None, tokenUsage=None)
    except Exception as e:
        response = ProviderResponse(output=None, error=repr(e), tokenUsage=None)

    print("Successfully made a response.")
    return response.to_dict()


if __name__ == "__main__":
    persona = "doctor"
    text = """
    There are 3 valves inside the heart. The biggest is the aorta. This is the main part that can go wrong.
    """
    result = call_api(
        prompt=f"You are a {persona}. Give me a raw json encoded list of health claims in the following text: {text}",
        options={},
        context={
            "vars": {
                "persona": persona,
                "text": text,
            }
        },
    )

    print(result)
