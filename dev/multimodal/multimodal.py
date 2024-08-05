from gemini import GeminiModel
from prompts import MULTIMODAL_RAPHAEL_PROMPT

from health_misinfo_shared.data_parsing import parse_model_json_output


class MultiModalRaphael:
    def __init__(self) -> None:
        self.model = GeminiModel()
        self.prompt = MULTIMODAL_RAPHAEL_PROMPT

    def analyse_video(self, video_uri: str):
        model_output = self.model.run_prompt_on_video(self.prompt, video_uri)
        output_dict = parse_model_json_output(model_output)
        return output_dict
