@echo off
SETLOCAL

echo [INFO] Subindo container do backend...
docker-compose up -d --build

timeout /T 5 /NOBREAK >nul

echo [INFO] Copiando .jar do container para host...
docker cp backingtracker-server-container:/backingtracker/client.jar client.jar

echo [INFO] Iniciando cliente...
java -jar client.jar

echo [INFO] Cliente fechado, parando container...
docker-compose down

ENDLOCAL