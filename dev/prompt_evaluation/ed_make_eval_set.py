import pandas as pd


evaluation = [
    {
        "text": "The male human has two hearts. The first is in its chest, and the second is in its head. They pump blood around the body. I am a human.",
        "claims": """[
            "The male human has two hearts",
            "The first human heart is in the chest",
            "the second human heart is in the head",
            "hearts pump blood around the body"
        ]""",
    },
    {
        "text": "there are no medical claims in this text.",
        "claims": "[]",
    },
    {
        "text": "Vaccines are not effective. The Covid vaccine has killed millions. You shouldn't get it.",
        "claims": """[
            "Vaccines are not effective",
            "The Covid vaccine has killed millions"
        ]""",
    },
]


if __name__ == "__main__":
    df = pd.DataFrame(evaluation)
    df.to_json("dev/prompt_evaluation/autosxs_eval.jsonl", lines=True, orient="records")
