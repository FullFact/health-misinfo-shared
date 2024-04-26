import pandas as pd
import numpy as np
import csv
from sklearn.metrics import precision_recall_fscore_support
from rouge_score import rouge_scorer
from vertexai.language_models import TextGenerationModel
from health_misinfo_shared import fine_tuning


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


def explain_build_results_table(
    model: TextGenerationModel, target_data: pd.DataFrame
) -> pd.DataFrame:
    """Simple evaluation of 'explaination'-type model by feeding labelled set into model.
    Return a full table of results comparing target set and model outputs."""
    # TODO: use a separate hold-out evaluation set instead of training set

    # we only want to pass each chunk to model once! So group by chunk
    target_grps = target_data.groupby("chunk")
    all_responses = []
    all_results = []

    for chunk, target_grp in target_grps:
        batch_results = []
        # should be list of length 1 as we only pass in one chunk:
        responses = fine_tuning.get_video_responses(model, [chunk])
        # print(f"responses {len(responses)=}   {len(responses[0]['response'])=}")
        all_responses += responses
        # Step through responses, which should be dict of claim, explanation
        # and for each one, find the claim in the _training_data group and compare the explanation
        # Want to measure fine-grained label-matches and coarse-grained (checkworthy vs not-c.w.)
        # We'll need a table with every target_claim and every response_claim (whether it matches or not)
        for response in responses[0].get("response", []):
            response_claim = response["claim"]
            response_explanation = response["explanation"]

            targs = list(target_grp["claim"].values)
            best_idx = closest_rouge(response_claim, targs)
            this_result = {
                "response_claim": response_claim,
                "response_explanation": response_explanation,
            }
            if best_idx >= 0:
                print(f"Model claim:      \t{response_claim}")
                print(f"Model explanation \t{response_explanation}")
                print(f"Closest target:   \t{targs[best_idx]}")
                print(
                    f"Target explanation: \t{target_grp.iloc[best_idx]['explanation']}"
                )
                print(
                    f'Label match? {target_grp.iloc[best_idx]["explanation"] == response_explanation}'
                )
                this_result["target_claim"] = targs[best_idx]
                this_result["target_explanation"] = target_grp.iloc[best_idx][
                    "explanation"
                ]
            else:
                this_result["target_claim"] = ""
                this_result["target_explanation"] = ""
            batch_results.append(this_result)
            print()
        for id, targ in target_grp.iterrows():
            already_matched = [
                b for b in batch_results if b["target_claim"] == targ["claim"]
            ]
            if not already_matched:
                # Add in any targets that were not matched by this batch of responses
                this_result = {
                    "target_claim": targ["claim"],
                    "target_explanation": targ["explanation"],
                    "response_claim": "",
                    "response_explanation": "",
                }
                batch_results.append(this_result)
        all_results.extend(batch_results)
    df_results = pd.DataFrame(all_results)
    print(f"Got model results with {df_results.shape[0]} rows.")

    return df_results


def evaluate(results: pd.DataFrame) -> dict:
    """Calculate P,R,F1 etc. from a set of results comparing target and model outputs"""
    # Input data frame will have columns:
    # "response_claim" "response_explanation" "target_claim" "target_explanation"

    # We need to check the label type: if the response is missing, replace it with "nothing to check"
    # Then map reponse_explanation and target_expalnation onto CHECKWORTHY_EXPLANATIONS or UNCHECKWORTHY_EXPLANATIONS
    # and then calculate TP,FP etc.
    checkworthy_pattern = "|".join(fine_tuning.CHECKWORTHY_EXPLANATIONS)
    # List of claims that should have been labelled as True (=Checkworthy)
    cw_targ = results["target_explanation"].str.contains(checkworthy_pattern)
    cw_targ = cw_targ.fillna(False)

    # List of claims that were labelled by the model as True (=Checkworthy)
    cw_response = results["response_explanation"].str.contains(checkworthy_pattern)
    cw_response = cw_response.fillna(False)

    # Optionally store ressults in a table:
    # scores_df=pd.DataFrame({"response":cw_response,"target":cw_targ})

    # setting average="binary" means only report scores for the "True" class
    precision, recall, f1, _support = precision_recall_fscore_support(
        cw_targ, cw_response, average="binary"
    )

    metrics = {"f1": f1, "precision": precision, "recall": recall}
    return metrics


def explain_eval(target_data: pd.DataFrame) -> dict:
    """ "Take a dataframe with some labelled chunks / claims.
    Pass them through the fine-tuned model.
    Compare the model predictions to the provided labels.
    Calculate & return precision, recall, f1."""
    model = fine_tuning.get_model_by_display_name("dc_tuned_explain_0")

    raw_results = explain_build_results_table(model, target_data)
    raw_results.to_csv("eval_results.csv", quoting=csv.QUOTE_ALL)
    metrics_results = evaluate(raw_results)

    return metrics_results


if __name__ == "__main__":
    # pass some of the training set back through the model:
    _target_data = pd.read_csv("data/training_set_v2.csv")
    print(f"loaded {_target_data.shape[0]} records")

    # df_results = pd.read_csv("eval_results.csv")
    # _metrics_results = evaluate(df_results)
    _metrics_results = explain_eval(_target_data)
    print(_metrics_results)
