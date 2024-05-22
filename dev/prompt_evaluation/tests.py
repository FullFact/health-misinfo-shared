import pandas as pd

test_text = "There are 3 valves inside the heart. The biggest is the aorta. This is the main part that can go wrong."

tests = [
    {
        "persona": "doctor",
        "text": test_text,
    },
    {
        "persona": "a caveman who can only answer in sentences made of one syllable words",
        "text": test_text,
    },
]


if __name__ == "__main__":
    # make the tests csv
    test_df = pd.DataFrame(tests)
    test_df.to_csv("dev/prompt_evaluation/tests.csv", index=False)
