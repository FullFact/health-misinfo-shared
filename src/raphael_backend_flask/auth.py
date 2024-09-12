from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

from raphael_backend_flask.db import execute_sql

auth = HTTPBasicAuth()


class User:
    def __init__(self, user_id: int, username: str, admin: int):
        self.user_id: int = user_id
        self.username: str = username
        self.roles: list[str] = ["admin"] if admin else []


def create_user_sql(username: str, password: str, admin: bool) -> None:
    hashed = generate_password_hash(password)
    execute_sql(
        "INSERT INTO users (username, password_hash, admin) VALUES (?, ?, ?)",
        (
            username,
            hashed,
            1 if admin else 0,
        ),
    )


def update_user_password_sql(username: str, password: str) -> None:
    hashed = generate_password_hash(password)
    execute_sql(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (
            hashed,
            username,
        ),
    )


def disable_user_sql(username: str) -> None:
    execute_sql("UPDATE users SET password_hash = NULL WHERE username = ?", (username,))


@auth.verify_password
def verify_pass(username: str, password: str) -> User | None:
    res = execute_sql(
        "SELECT id, password_hash, admin FROM users WHERE username = ? AND password_hash IS NOT NULL",
        (username,),
    )
    if len(res) < 1:
        return None

    hashed = res[0]["password_hash"]
    if check_password_hash(hashed, password):
        return User(user_id=res[0]["id"], username=username, admin=res[0]["admin"])

    return None


@auth.get_user_roles
def get_user_roles(user: User) -> list[str]:
    return user.roles
