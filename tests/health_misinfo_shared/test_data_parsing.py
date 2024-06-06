from pytest import mark, param
from health_misinfo_shared.data_parsing import parse_model_json_output


@mark.parametrize(
    "model_output,expected,should_fail",
    [
        param(
            """
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            ]
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            False,
            id="perfect case",
        ),
        param(
            """
            json```
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            ]```
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            False,
            id="prefixed with json, surrounded by backticks",
        ),
        param(
            """
            json```
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            ]
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            False,
            id="missing final backticks",
        ),
        param(
            """
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            ]```
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            False,
            id="only backticks at the end",
        ),
        param(
            """
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            True,
            id="missing closing brace",
        ),
        param(
            """
                {"claim": "claim 1"},
                {"claim": "claim 2"}
            ]
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            True,
            id="missing opening brace",
        ),
        param(
            """
            Claim: Claim 1
            Claim: Claim 2
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            True,
            id="not json",
        ),
        param(
            """
            [
                {'claim': 'claim 1'},
                {'claim': 'claim 2'}
            ]
            """,
            [
                {"claim": "claim 1"},
                {"claim": "claim 2"},
            ],
            False,
            id="single quotes",
        ),
    ],
)
def test_parse_model_json_output(
    model_output: str, expected: list[dict[str, str]], should_fail: bool
):
    try:
        assert parse_model_json_output(model_output) == expected and not should_fail
    except Exception:
        assert should_fail
