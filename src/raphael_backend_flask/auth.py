import os

from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

auth = HTTPBasicAuth()
users = {
    user: generate_password_hash(password)
    for user, password in (
        item.split(":") for item in os.environ["USERS"].split(",") if item
    )
}


@auth.verify_password
def verify_password(username: str, password: str) -> str | None:
    if username in users and check_password_hash(users[username], password):
        return username
    return None
