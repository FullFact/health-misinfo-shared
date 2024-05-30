import json
import pprint
import pandas as pd
import numpy as np
from typing import Any
from sklearn.metrics import precision_recall_fscore_support
from rouge_score import rouge_scorer


CHECKWORTHY_SUMMARIES = ["worth checking", "may be worth checking"]


def closest_rouge(pred: str, targs: list[str]) -> float:
    """Take one predicted claim and find the nearest target claim from a list.
    Returns the index of the best match if its score is above a threshold.
    If no match is good, return -1"""
    rouge_type = "rouge1"
    scorer = rouge_scorer.RougeScorer([rouge_type], use_stemmer=False)

    score_dicts = [scorer.score(t, pred) for t in targs]

    index = np.argmax([s[rouge_type].fmeasure for s in score_dicts])
    max_score = score_dicts[index]

    # Apply a loose threshold then return best-match of what's left
    f_threshold = 0.5
    if max_score[rouge_type].fmeasure > f_threshold:
        return index
    else:
        print(f"ROUGE match is below threshold: score {max_score[rouge_type].fmeasure}")
        print(f"\ttarg {targs[index]}\n\tpred {pred}")
        return -1


def make_results_table(
    generated_output: list[dict[str, Any]], expected_output: list[dict[str, Any]]
) -> pd.DataFrame:
    results = []
    for generated_claim in generated_output:
        response_claim = generated_claim["claim"]
        response_explanation = generated_claim["labels"]["summary"]

        targs = [claim["claim"] for claim in expected_output]

        best_idx = closest_rouge(response_claim, targs)
        this_result = {
            "response_claim": response_claim,
            "response_explanation": response_explanation,
        }
        if best_idx >= 0:
            this_result["target_claim"] = targs[best_idx]
            this_result["target_explanation"] = expected_output[best_idx]["labels"][
                "summary"
            ]
        else:
            this_result["target_claim"] = ""
            this_result["target_explanation"] = ""
        results.append(this_result)

    for expected_claim in expected_output:
        already_matched = [
            b for b in results if b["target_claim"] == expected_claim["claim"]
        ]
        if not already_matched:
            # Add in any targets that were not matched by this batch of responses
            this_result = {
                "target_claim": expected_claim["claim"],
                "target_explanation": expected_claim["labels"]["summary"],
                "response_claim": "",
                "response_explanation": "",
            }
            results.append(this_result)

    return pd.DataFrame(results)


def evaluate(results: pd.DataFrame) -> dict[str, Any]:
    """Calculate P,R,F1 etc. from a set of results comparing target and model outputs"""
    # Input data frame will have columns:
    # "response_claim" "response_explanation" "target_claim" "target_explanation"

    # We need to check the label type: if the response is missing, replace it with "nothing to check"
    # Then map reponse_explanation and target_expalnation onto CHECKWORTHY_EXPLANATIONS or UNCHECKWORTHY_EXPLANATIONS
    # and then calculate TP,FP etc.
    # List of claims that should have been labelled as True (=Checkworthy)
    cw_targ = results["target_explanation"].isin(CHECKWORTHY_SUMMARIES)
    cw_targ = cw_targ.fillna(False)

    # List of claims that were labelled by the model as True (=Checkworthy)
    cw_response = results["response_explanation"].isin(CHECKWORTHY_SUMMARIES)
    cw_response = cw_response.fillna(False)

    # Optionally store ressults in a table:
    # scores_df=pd.DataFrame({"response":cw_response,"target":cw_targ})

    # setting average="binary" means only report scores for the "True" class
    precision, recall, f1, _support = precision_recall_fscore_support(
        cw_targ, cw_response, average="binary"
    )

    metrics = {"f1": f1, "precision": precision, "recall": recall}
    return metrics


def get_assert(output: str, context: dict[str, Any]) -> bool | float | dict[str, Any]:
    prompt = context["prompt"]
    variables = context["vars"]

    generated_output = json.loads(output)
    expected_output = json.loads(variables["expected_output"])

    results_table = make_results_table(generated_output, expected_output)
    metrics = evaluate(results_table)

    # This return is an example GradingResult dict
    return {
        "pass": bool(metrics["f1"] > 0.5),
        "score": float(metrics["f1"]),
        "reason": pprint.pformat(metrics),
    }


if __name__ == "__main__":
    test_generated_output = """
    [
        {
            "claim": "The sky is blue.",
            "original_text": "As we all know, it is blue",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        },
        {
            "claim": "mushrooms cure cancer",
            "original_text": "mushrooms cure cancer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "high harm",
                    "summary": "worth checking"
                }
        },
        {
            "claim": "Eating walnuts will make you live longer",
            "original_text": "Eating walnuts will make you live longer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "low harm",
                    "summary": "may be worth checking"
                }
        }
    ]
    """.strip()

    test_expected_output = """
    [
        {
            "claim": "The sky is blue.",
            "original_text": "As we all know, it is blue",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        },
        {
            "claim": "mushrooms cure cancer",
            "original_text": "mushrooms cure cancer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "high harm",
                    "summary": "worth checking"
                }
        },
        {
            "claim": "The writer has a dog called Geoff",
            "original_text": "I have a dog called Geoff",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "not medical",
                    "support": "uncontroversial statement",
                    "harm": "harmless",
                    "summary": "not worth checking"
                }
        },
        {
            "claim": "Eating walnuts will make you live longer",
            "original_text": "Eating walnuts will make you live longer",
            "labels":
                {
                    "understandability": "understandable",
                    "type_of_claim": "statement of fact",
                    "type_of_medical_claim": "cause/effect",
                    "support": "novel claim",
                    "harm": "low harm",
                    "summary": "may be worth checking"
                }
        }
    ]
    """.strip()

    output = get_assert(
        test_generated_output,
        context={
            "prompt": "PROMPT",
            "vars": {"expected_output": test_expected_output},
        },
    )
    pprint.pp(output)
