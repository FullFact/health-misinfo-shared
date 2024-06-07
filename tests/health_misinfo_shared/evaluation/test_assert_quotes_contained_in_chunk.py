from pytest import mark, param
from typing import Any
from evaluation.assert_quotes_contained_in_chunk import (
    check_quote_in_chunk,
    make_reason,
)

EXAMPLE_CHUNK = "this is an example of a chunk that might come from the transcript it is unpunctuated and terrible"


@mark.parametrize(
    "quote,chunk,expected_pass",
    [
        param("this is an example of a chunk", EXAMPLE_CHUNK, True),
        param("THIS is an Example of a Chunk", EXAMPLE_CHUNK, True),
        param('this, is an example of a "chunk".', EXAMPLE_CHUNK, True),
        param("this here is an example of a chunk", EXAMPLE_CHUNK, False),
        param("bears no resemblance at all", EXAMPLE_CHUNK, False),
    ],
)
def test_check_quote_in_chunk(quote: str, chunk: str, expected_pass: bool):
    assert check_quote_in_chunk(quote, chunk) == expected_pass


@mark.parametrize(
    "claims,passes_list,chunk,expected_reason",
    [
        param(
            [
                {"original_text": "this is an example"},
                {"original_text": "of a chunk"},
            ],
            [True, True],
            EXAMPLE_CHUNK,
            "The following quotes are not contained in the chunk:\n[]",
            id="everything is there",
        ),
        param(
            [
                {"original_text": "this is an example"},
                {"original_text": "of a segment"},
            ],
            [True, False],
            EXAMPLE_CHUNK,
            "The following quotes are not contained in the chunk:\n['of a segment']",
            id="one claim doesn't match",
        ),
    ],
)
def test_make_reason(
    claims: list[dict[str, Any]],
    passes_list: list[bool],
    chunk: str,
    expected_reason: str,
):
    reason = make_reason(claims, passes_list, chunk)
    assert reason == expected_reason
