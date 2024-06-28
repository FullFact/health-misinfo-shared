import pytest
from pytest import mark, param

from health_misinfo_shared.claim_format_checker import (
    assert_output_json_format,
    insert_missing_key_as_null,
)


@mark.parametrize(
    "output, expected_bool",
    [
        param(
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            True,
            id="correctly formatted",
        ),
        param(
            {
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            False,
            id="missing claim",
        ),
        param(
            {
                "claim": "apples help you levitate",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            False,
            id="missing original_text",
        ),
        param(
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            False,
            id="missing a label",
        ),
    ],
)
def test_assert_output_json_format(output, expected_bool):
    assert assert_output_json_format(output) == expected_bool


@mark.parametrize(
    "output, expected_amended",
    [
        param(
            {
                "claim": "apples help you levitate",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            {
                "claim": "apples help you levitate",
                "original_text": "not found",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "a serious one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            id="original_text missing",
        ),
        param(
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "loud and clear",
                    "type_of_claim": "a bad one",
                    "type_of_medical_claim": "",
                    "support": "none at all",
                    "harm": "too much",
                },
            },
            id="one label missing",
        ),
        param(
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
            },
            {
                "claim": "apples help you levitate",
                "original_text": "eating an apple regularly will allow you to float away",
                "labels": {
                    "understandability": "",
                    "type_of_claim": "",
                    "type_of_medical_claim": "",
                    "support": "",
                    "harm": "",
                },
            },
            id="one label missing",
        ),
    ],
)
def test_insert_missing_value(output, expected_amended):
    assert insert_missing_key_as_null(output) == expected_amended
