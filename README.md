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


## Create a database

Run `python3 -m tools.db` to plonk database.db into the current directory. If any table already exists it will raise an Exception and quit.

## Deploy/update a server

Install Ansible. Install the necessary roles with `ansible-galaxy install -r ansible/requirements.yml`.

Write the IP of the target server to a file, i.e. `hosts`:
```
<target host ip>
```

To deploy the backend, look at .env.backend.example and copy that to the .env.backend. Put in a user:pass everyone can know, or a couple.

Run `ansible-playbook -i hosts ansible/playbooks/nginx_docker.yaml` to deploy the reverse proxy to that IP address. You will need SSH access to the host. This only needs to be done once.
Run `ansible-playbook -i hosts ansible/playbooks/docker_deploy.yaml -e pwd=$PWD` to update and deploy the frontend and backend to that IP address. You will need SSH access to the host.
