FROM python:3.10-slim

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN pip install poetry gunicorn
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

COPY src/health_misinfo_shared ./health_misinfo_shared
COPY src/raphael_backend_flask ./raphael_backend_flask
COPY .env ./.env
COPY data ./data

EXPOSE 3000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DB_PATH=/app/data/database.db
CMD ["gunicorn", "raphael_backend_flask.app:app", "--config", "raphael_backend_flask/gunicorn_config.py"]
