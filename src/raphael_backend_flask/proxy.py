import os
import random

PROXY_COUNT = int(os.environ["PROXY_COUNT"])
PROXY_USERNAME = os.environ["PROXY_USERNAME"]
PROXY_PASSWORD = os.environ["PROXY_PASSWORD"]
PROXY_DOMAIN = os.environ["PROXY_DOMAIN"]


def get_proxy_url() -> str:
    proxy_id = random.randrange(1, PROXY_COUNT, 1)
    return f"http://{PROXY_USERNAME}-{proxy_id}:{PROXY_PASSWORD}@{PROXY_DOMAIN}/"
