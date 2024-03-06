# health-misinfo-shared
Raphael health misinformation project, respository shared by Full Fact and Google 

## Getting captions

Use `youtube_api.py` to search by keywords and extract captions to a local filestore. Currently set up to prefer English-language captions, though we should aim to be language agnostic in production.

## Extract claims

Use `vertex.py` to load in a set of captions and pass to a off-the-shelf LLM (e.g. Gemini) to identify health-related claims. This can be used to create a spreadsheet for manual-labelling of noteworthy claims.

## Fine-tuning

Use `fine_tuning.py` to fine-tune a model and get responses from it.

`make_training_set()` loads a CSV file of training data and re-format, ready to fine-tune a model.

`tuning()` carry out the fine-tuning.

`get_video_responses()` use a fine-tuned to generate reponses to the transcript of a video.


