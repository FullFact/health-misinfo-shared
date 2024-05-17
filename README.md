# Raphael health misinformation project

(Respository shared by Full Fact and Google for work on a proof-of-concept)

## Getting started

To run the app locally, you’ll need python, poetry and node installed. Then:

1. Install backend dependencies:
   ```
   poetry install --no-root
   ```
2. Install frontend dependencies
   ```
   npm --prefix src/raphael_frontend_react install
   ```

To start the development servers:

1. Start the backend development server with:
   ```
   PYTHONPATH=src USERS=ff:changeme poetry run python -m raphael_backend_flask.app
   ```
2. Start the frontend development server with:
   ```
   REACT_APP_BASE_URL=http://localhost:3000/api PORT=4000 npm --prefix src/raphael_frontend_react start
   ```
3. In a browser, visit http://localhost:4000. Login details are: `ff` / `changeme`.

### Running locally with Docker

Very roughly:

```
cp .env.example .env  # and populate this
docker build -t fullfact/raphael-backend:latest -f Dockerfile.backend .
docker build -t fullfact/raphael-frontend:latest -f Dockerfile.frontend .
docker compose up -d
```

## Downloading some captions

Use `youtube_api.py` to search by keywords and extract captions to a local filestore, in `data/captions`. Currently set up to prefer English-language captions, though we should aim to be language agnostic in production. The location of the `CLIENT_SECRETS_FILE` needs to be set as an environment variable. ([How to get the credentials](https://developers.google.com/youtube/v3/quickstart/python))

## Extract claims

Use `vertex.py` to load in a set of captions and pass to a off-the-shelf LLM (e.g. Gemini) to identify health-related claims. This can be used to create a spreadsheet for manual-labelling of noteworthy claims.

## Fine-tuning

Use `fine_tuning.py` to fine-tune a model and get responses from it.

`make_training_set()` loads a CSV file of training data and re-format, ready to fine-tune a model.

`tuning()` carries out the fine-tuning. This starts a remote job that takes c.45 minutes.

`get_video_responses()` uses a fine-tuned model to generate reponses to the transcript of a video.

## Model types

**simple-type** model: given a transcript, it is trained to return a list of harmful health-related claims 

**explaination-type** model: given a transcript, it is trained to return a list of health-related claims with an explanation label predicting how checkworthy it is and why. These labels (for concepts like "high harm", "cites study" etc.) allow us to add expert knowledge into the training data.

## Deploy/update a server

For code changes, branches are deployed via a GitHub Actions workflow dispatch.

The process for making nginx changes is a bit more involved:

1. Install Ansible. Install the necessary roles:
   ```
   poetry run ansible-galaxy install -r ansible/requirements.yml
   ```
2. Run:
   ```
   poetry run ansible-playbook -i ansible/inventories/hosts ansible/playbooks/nginx_docker.yaml
   ```

## Getting claims for YouTube captions

For building a set of labelled data, we want to get health claims, without all the other stuff we're predicting.
The `find_claims_within_captions.py` script takes our downloaded YouTube captions and asks Gemini to find all the claims contained within.

> Note on Gemini 1.5: to use this version you have to specify `gemini-1.5-pro-preview-0409` rather than just `gemini-1.5-pro` like you would for 1.0.

## Writing new prompts

We introduce all prompts with a persona, outlining that the model will be acting as a specialist health fact-checker. If new prompts are written, ensure the following passage is added to the front:

> You are a specialist health fact-checker.
>
> You must always prioritise accuracy, and never give a response you cannot be certain of, because you know there are consequences to spreading misinformation, even unintentionally.
>
> You would always rather say that you do not know the answer than say something which might be incorrect.
