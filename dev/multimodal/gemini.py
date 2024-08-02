import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.generative_models import GenerativeModel, Part


DEFAULT_PROJECT = "exemplary-cycle-195718"

DEFAULT_SAFETY_SETTINGS = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_NONE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_NONE,
}

VIDEO_SAFETY_SETTINGS = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}


class GeminiModel:
    DEFAULT_MODEL = "gemini-1.5-flash-001"
    DEFAULT_LOCATION = "europe-west2"

    def __init__(
        self,
        project: str = DEFAULT_PROJECT,
        location: str = DEFAULT_LOCATION,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        self.model: GenerativeModel = self.load_model(project, location, model_name)

        self.parameters = {
            "candidate_count": 1,
            "max_output_tokens": 8192,
            "temperature": 0,
            "top_p": 1,
        }
        self.safety_settings = DEFAULT_SAFETY_SETTINGS
        self.safety_settings_video = VIDEO_SAFETY_SETTINGS

    def load_model(
        self, project: str, location: str, model_name: str
    ) -> GenerativeModel:
        vertexai.init(project=project, location=location)
        return GenerativeModel(model_name=model_name)

    def run_prompt(self, prompt: str) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config=self.parameters,
            safety_settings=self.safety_settings,
        )
        if not len(response.candidates):
            raise Exception(
                f"No model output: possible reason: {response.prompt_feedback}"
            )
        candidate = response.candidates[0]
        return candidate.text

    def run_prompt_on_video(self, prompt: str, video_path: str) -> str:
        """
        Runs a prompt over a given video. Used for multimodal analysis.

        Parameters
        ----------
        prompt: str
            The text prompt.
        video_path: str
            The path of the video you want to process.
            A Google Storage URI (prefixed by 'gs://')

        Returns
        -------
        The text output of the Gemini model.
        """
        response = self.model.generate_content(
            [
                Part.from_uri(video_path, mime_type="video/mp4"),
                prompt,
            ],
            generation_config=self.parameters,
            safety_settings=self.safety_settings_video,
        )
        if not len(response.candidates):
            raise Exception(
                f"No model output: possible reason: {response.prompt_feedback}"
            )
        candidate = response.candidates[0]
        return candidate.text


if __name__ == "__main__":
    model = GeminiModel()

    output = model.run_prompt(
        "Write a haiku about being unable to remember an aquaintance's name."
    )

    print(output)

    output = model.run_prompt_on_video(
        "Write a haiku about this video.",
        "gs://fullfact-nlp/raphael/videos/7300977537717407022.mp4",
    )

    print(output)
