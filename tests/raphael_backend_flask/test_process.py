import pytest

from raphael_backend_flask import transcript

input_transcript = [
    {"start": 0.04, "sentence_text": "2020 the world was turned upside down"},
    {"start": 2.679, "sentence_text": "when covid-19 took over now four years"},
    {"start": 6.24, "sentence_text": "later the conversation continues as a"},
    {"start": 8.4, "sentence_text": "new strain makes its debut kp3 western"},
    {"start": 11.519, "sentence_text": "Mass news reporter Olivia hickey joins"},
    {"start": 13.36, "sentence_text": "us live in studio with more Olivia Happ"},
    {"start": 15.679, "sentence_text": "be Chris I spoke with pediatrician Dr"},
    {"start": 17.64, "sentence_text": "John Kelly today he explains like"},
    {"start": 19.76, "sentence_text": "influenza different strains of covid"},
    {"start": 21.6, "sentence_text": "Peak at different times and why this is"},
    {"start": 24.199, "sentence_text": "why he says it's important to stay up to"},
    {"start": 25.88, "sentence_text": "date on vaccines one parent I spoke with"},
    {"start": 28.76, "sentence_text": "is on the same page Abby Downing recalls"},
    {"start": 31.519, "sentence_text": "her experience during the early days of"},
    {"start": 33.64, "sentence_text": "the covid-19 pandemic we had our first"},
    {"start": 35.96, "sentence_text": "child actually 6 months into Co so it"},
    {"start": 37.96, "sentence_text": "certainly was very challenging and our"},
    {"start": 39.6, "sentence_text": "second child in January of 2022 so still"},
]


@pytest.mark.parametrize(
    "sentence,offset_start_s,offset_end_s",
    [
        [
            "he explains like influenza different strains of covid Peak at different "
            "times and why this is why he says it's important to stay up to date on "
            "vaccines",
            17.64,
            28.76,
        ],
        [
            "experience during the early days",
            31.519,
            33.64,
        ],
        [
            "our second child in January of 2022",
            37.96,
            None,
        ],
    ],
)
def test_refine_offsets(sentence, offset_start_s, offset_end_s):
    claim = {
        "raw_sentence_text": sentence,
        "offset_start_s": 0.04,
        "offset_end_s": None,
    }
    result = transcript.refine_offsets(claim, input_transcript)
    assert result["offset_start_s"] == offset_start_s
    assert result["offset_end_s"] == offset_end_s
