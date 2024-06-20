from pytest import mark, param
from health_misinfo_shared import fine_tuning


@mark.parametrize(
    "chunk,expected_harm",
    [
        param(
            "It is well known that cucumbers cure cancer if used correctly.",
            "high harm",
        ),
        param(
            "It is well known that cucumbers taste bland even if used correctly.",
            "harmless",
        ),
    ],
)
def test_model_harm(chunk: str, expected_harm: str):
    model = fine_tuning.get_model_by_display_name("dc_tuned_explain_0")

    chunk_dict = {"text": chunk}

    model_output = [
        r["response"][0]
        for r in fine_tuning.get_video_responses(model, [chunk_dict], multilabel=True)
    ]

    assert model_output[0]["labels"]["harm"] == expected_harm
