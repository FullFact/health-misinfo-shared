#! /bin/bash

echo "Downloading YouTube captions"

PYTHONPATH=/src CLIENT_SECRETS_FILE=~/.youtube-key.json OAUTHLIB_INSECURE_TRANSPORT=1 python src/health_misinfo_shared/youtube_api.py

echo "Finished running"