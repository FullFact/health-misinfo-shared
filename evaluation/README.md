# Evaluation

This directory contains code for evaluating our prompts using promptfoo.

## How to run evaluation

1. Check `promptfooconfig.yaml` and check that it's referring to the prompts and tests you want to run.
Tests are found in `tests.csv` by default, and prompts in the specified test files.
For comparing context vs no context, I wrote a file (`comparing_prompt_with_and_without_context.py`) which generates the prompt files and the tests for that specific case.
2. Make sure you're inside the evaluation directory and run the following. This will run the evaluation, and generate your results.
When it finishes, a nice colourful table will be printed in your terminal.

        npx promptfoo@latest eval

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

Remember to put it in an `__evaluationN` column in your `tests.csv` file.