FROM node:20 AS frontend-builder
LABEL authors="Francisco Lucas"

WORKDIR /web_client
COPY web_client/package.json web_client/package-lock.json ./
RUN npm ci
COPY web_client/ ./
RUN npm run build

FROM python:3.10-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Setting large ammount of timeout.
# For some reason "scypi" was taking more time then expected to be downloaded.
ENV UV_HTTP_TIMEOUT=600

# Installing useful/needed stuff in the container
RUN apt-get update
RUN apt-get install -y ffmpeg
RUN apt-get install -y curl
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Retrieves the needed files to build/run the python server with UV
COPY pyproject.toml /app
COPY uv.lock /app
COPY server /app/server

# Install the dependencies (deterministic based on the lock file)
RUN uv sync --frozen

# TODO: manually force download pretrained_models in this stage

COPY --from=frontend-builder /web_client/dist ./frontend/dist
RUN ln -s /app/.venv/bin/celery /usr/local/bin/celery

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]