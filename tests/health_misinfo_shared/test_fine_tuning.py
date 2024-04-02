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
            ]
        ],
        columns=["claim", "chunk", "explanation"],
    )

    df_results = evaluation.explain_build_results_table(model, target_data)
    print(df_results)
