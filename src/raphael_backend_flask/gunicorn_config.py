from raphael_backend_flask.db import run_migrations

bind = "0.0.0.0:3000"
workers = 4
timeout = 1800


def on_starting(server):
    print("LOLOLO")
    run_migrations()
