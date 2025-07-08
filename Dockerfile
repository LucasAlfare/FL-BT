FROM python:3.10-slim

LABEL authors="Francisco Lucas"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && \
    apt-get install -y openjdk-17-jdk ffmpeg && \
    apt-get clean

WORKDIR /build

COPY desktop_client /build/desktop_client

WORKDIR /build/desktop_client
RUN chmod +x ./gradlew && ./gradlew packageReleaseUberJarForCurrentOS --no-daemon

RUN mkdir -p /backingtracker && \
    cp ./app/build/compose/jars/FLBTClient-windows-x64-1.0.0-release.jar /backingtracker/client.jar

WORKDIR /app
COPY server/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY server/ .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000"]