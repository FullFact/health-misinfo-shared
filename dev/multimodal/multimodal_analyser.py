from typing import Any
from multimodal.gemini import GeminiModel
from multimodal.prompts import MULTIMODAL_RAPHAEL_PROMPT

from health_misinfo_shared.data_parsing import parse_model_json_output  # type: ignore
from health_misinfo_shared.label_scoring import get_claim_summary  # type: ignore


class MultiModalRaphael:
    def __init__(self) -> None:
        self.model = GeminiModel()
        self.prompt = MULTIMODAL_RAPHAEL_PROMPT

    def analyse_video(self, video_uri: str) -> dict[str, Any]:
        model_output = self.model.run_prompt_on_video(self.prompt, video_uri)
        output_parsed = parse_model_json_output(model_output)
        for claim in output_parsed:
            claim["labels"]["summary"] = get_claim_summary(claim["labels"])
        return output_parsed


if __name__ == "__main__":
    from pprint import pp

    analyser = MultiModalRaphael()
    output = analyser.analyse_video(
        "gs://fullfact-nlp/raphael/videos/7328225789827190059.mp4"
    )

    pp(output)
