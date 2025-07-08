FROM python:3.10-slim
LABEL authors="Francisco Lucas"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app

COPY server/requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY server/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]