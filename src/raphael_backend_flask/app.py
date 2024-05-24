from dotenv import find_dotenv, load_dotenv

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

app = Flask(__name__)
CORS(app)
app.register_blueprint(routes)
app.secret_key = os.urandom(12).hex()


@app.teardown_appcontext
def teardown_db_connection(_: Any) -> None:
    conn: Connection | None = g.get("_database")
    if conn:
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
