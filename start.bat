@echo off
SETLOCAL

IF EXIST client.jar (
    echo [INFO] client.jar já existe, pulando build do client.
) ELSE (
    echo [INFO] Buildando client.jar via Docker...
    docker build -f Dockerfile.client -t client-builder .
    docker create --name temp-client client-builder
    docker cp temp-client:/out/client.jar client.jar
    docker rm temp-client
)

echo [INFO] Subindo container do backend...
docker-compose up -d --build

timeout /T 5 /NOBREAK >nul

echo [INFO] Iniciando cliente...
java -jar client.jar

echo [INFO] Cliente fechado, parando container...
docker-compose down

ENDLOCAL