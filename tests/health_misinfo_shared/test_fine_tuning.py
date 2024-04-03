import pandas as pd
from health_misinfo_shared import fine_tuning, evaluation, prompts


def test_eval():

    model = fine_tuning.get_model_by_display_name("dc_tuned_explain_0")

    target_data = pd.DataFrame.from_records(
        data=[
            [
                "Cucumbers can cure cancer",
                "It is well known that cucumbers cure cancer if used correctly.",
                "high harm",
            ],
            [
                "Cucumbers can taste bland",
                "It is well known that cucumbers taste bland even if used correctly.",
                "nothing to check",
            ],
        ],
        columns=["claim", "chunk", "explanation"],
    )

    raw_results = evaluation.explain_build_results_table(model, target_data)
    metrics_results = evaluation.evaluate(raw_results)
    # print(raw_results)
    # print(metrics_results)
    assert metrics_results["precision"][0] == 1.0
    assert metrics_results["recall"][0] == 1.0
