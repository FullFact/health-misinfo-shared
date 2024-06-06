# Evaluation

This directory contains code for evaluating our prompts using promptfoo.

## How to run evaluation

1. Check the config `.yaml` file for the test you want to run and check that it's referring to the prompts and tests you want to run.
Tests are found in `tests.csv` by default, and prompts in the specified test files.
For comparing context vs no context, I wrote a file (`comparing_prompt_with_and_without_context.py`) which generates the prompt files and the tests for that specific case. 
It would be advisable to write a similar script for new tests, which would also generate prompt text files, and a `tests.csv` equivalent.
2. Make sure you're inside the evaluation directory and run the following. This will run the evaluation, and generate your results.
When it finishes, a nice colourful table will be printed in your terminal.

        npx promptfoo@latest eval -c YOUR_CONFIG_FILE.yaml

3. Run the following to view the results in your browser.

        npx promptfoo@latest view

## How to make a new assertion/test
When we define our test cases, we specify what assertions we want to apply.

Each assertion gives a pass/fail, and they can be simple things like "contains this substring" or "is in json format", or they can be more complicated, like asking an LLM if the output is a certain way.

We can also give a custom python script as an assertion.
This script must have a `get_assert` function, and be in the expected format promptfoo wants.
Here's an example:

```python
from typing import Dict, TypedDict, Union

def get_assert(output: str, context) -> Union[bool, float, Dict[str, Any]]:
    print('Prompt:', context['prompt'])
    print('Vars', context['vars']['topic'])

    # This return is an example GradingResult dict
    return {
      'pass': True,
      'score': 0.6,
      'reason': 'Looks good to me',
    }
```

So for each new way to compare output to evaluation data, you'll want a file like this.

Remember to put it in `__evaluationN` columns in your `tests.csv` file.

## Comparing something new
To make a new comparison, you'll want to make a few files:

1. `.txt` files for the prompts you want to compare.
2. a `tests.csv` file containing your test cases
3. a `.yaml` file defining the promptfoo config.

It's probably a good idea to make a python script (like `comparing_prompt_with_and_without_context.py`) which generates the first two.
For the `.yaml` file, just make a new one with a clear name, and it'll mostly be a copy and paste of the existing ones but swapping out the tests and prompts files.

## Evaluation data
We don't have perfect evaluation data at the moment.
For the current tests where we need labels, we've been using `data/test_eval_data_labelled_by_ed`, which is the training data, with a summary column added by me (**not a fact checker**) *very quickly*.

**This is not good, long term evaluation data**