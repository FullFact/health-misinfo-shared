This is a messy folder for trying things with prompt evaluation, using promptfoo and auto sxs.
Quick intro...

## PromptFoo
`promptfooconfig.yaml` tells promptfoo what to do.
Shouldn't need changing much because it basically just points to `ed_promptfoo_tests.py` for running the model, `prompt1.txt` for the prompt, and `tests.csv` for the tests.
Might want to add assertions, which basically set conditions to pass/fail tests.

`ed_promptfoo_tests.py` is the python script promptfoo uses to call the LLM API.
It's a python script because that means we can do whatever we want in there.
We could make a different script for each model if we had different models.
Minimum requirement is a function called `call_api` which takes that input and gives that output.

`tests.py` is a script for generating `test.csv`, a table of all the combinations of variables to give to the prompts.

`prompt1.txt` is a file with the prompt text in.
If we wanted multiple, I believe we can [separate them with ---](https://promptfoo.dev/docs/configuration/parameters#multiple-prompts-in-a-single-file).


### To run PromptFoo
> You'll need node.js installed for this to work.
> I wrote instructions for that in the Google doc report, I'll move them here at some point.

Make sure you're in the right environment and run this:

```
LOGLEVEL=debug npx promptfoo@latest eval
```

then to see a nice web interface for results, run this:

```
npx promptfoo@latest view
```

## AutoSxS

`ed_autosxs_tests.py` is a script for running AutoSxS. It should just run. It'll make some CSVs containing results.

`ed_make_eval_set.py` makes a dummy evaluation set for AutoSxS. The jsonl file it makes needs to go in a Google Cloud Bucket. The bucket used by `ed_autosxs_tests.py` should already have a file in it.

### To run Auto Side-by-Side (AutoSxS)

Run the script `ed_autosxs_tests.py`.