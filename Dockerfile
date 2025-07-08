FROM node:20 AS frontend-builder
WORKDIR /web_client
COPY web_client/package.json web_client/package-lock.json ./
RUN npm ci
COPY web_client/ ./
RUN npm run build

FROM python:3.10-slim AS backend

LABEL authors="Francisco Lucas"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY server/ .

COPY --from=frontend-builder /web_client/dist ./frontend/dist

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]