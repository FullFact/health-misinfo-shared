import random

from dotenv import find_dotenv, load_dotenv

from raphael_backend_flask.template_filters import format_offset, time_diff

try:
    load_dotenv(find_dotenv())
except Exception:
    pass

import os
from sqlite3 import Connection
from typing import Any

from flask import Flask, g
from flask_cors import CORS

from raphael_backend_flask.routes import routes

PROXY_COUNT = int(os.environ["PROXY_COUNT"])
PROXY_USERNAME = os.environ["PROXY_USERNAME"]
PROXY_PASSWORD = os.environ["PROXY_PASSWORD"]
PROXY_DOMAIN = os.environ["PROXY_DOMAIN"]

app = Flask(__name__)
CORS(app)
app.register_blueprint(routes)
app.secret_key = os.urandom(12).hex()
app.jinja_env.filters["format_offset"] = format_offset
app.jinja_env.filters["time_diff"] = time_diff


def get_proxy_url() -> str:
    proxy_id = random.randrange(1, PROXY_COUNT, 1)
    return f"http://{PROXY_USERNAME}-{proxy_id}:{PROXY_PASSWORD}@{PROXY_DOMAIN}/"


@app.teardown_appcontext
def teardown_db_connection(_: Any) -> None:
    conn: Connection | None = g.get("_database")
    if conn:
        conn.close()


if __name__ == "__main__":
    from raphael_backend_flask.db import run_migrations

    run_migrations()

    app.run(debug=True, host="0.0.0.0", port=3000)
