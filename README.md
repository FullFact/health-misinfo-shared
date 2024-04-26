# Raphael health misinformation project

(Respository shared by Full Fact and Google for work on a proof-of-concept)


## Downloading some captions

Use `youtube_api.py` to search by keywords and extract captions to a local filestore, in `data/captions`. Currently set up to prefer English-language captions, though we should aim to be language agnostic in production. The location of the `CLIENT_SECRETS_FILE` needs to be set as an environment variable. ([How to get the credentials](https://developers.google.com/youtube/v3/quickstart/python))


## Extract claims

Use `vertex.py` to load in a set of captions and pass to a off-the-shelf LLM (e.g. Gemini) to identify health-related claims. This can be used to create a spreadsheet for manual-labelling of noteworthy claims.

## Fine-tuning

Use `fine_tuning.py` to fine-tune a model and get responses from it.

`make_training_set()` loads a CSV file of training data and re-format, ready to fine-tune a model.

`tuning()` carries out the fine-tuning. This starts a remote job that takes c.45 minutes.

`get_video_responses()` uses a fine-tuned model to generate reponses to the transcript of a video.

## Getting claims for YouTube captions

For building a set of labelled data, we want to get health claims, without all the other stuff we're predicting.
The `find_claims_within_captions.py` script takes our downloaded YouTube captions and asks Gemini to find all the claims contained within.

> Note on Gemini 1.5: to use this version you have to specify `gemini-1.5-pro-preview-0409` rather than just `gemini-1.5-pro` like you would for 1.0.

