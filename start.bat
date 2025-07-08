@echo off
SETLOCAL

SET IMAGE_NAME=backingtracker_server
SET PORT=8000

docker image inspect %IMAGE_NAME% >nul 2>&1
IF ERRORLEVEL 1 (
    echo [INFO] Criando imagem Docker...
    docker build -t %IMAGE_NAME% -f server/Dockerfile .
)

echo [INFO] Iniciando servidor backend...
REM storing container ID to be properly closed later
FOR /F "usebackq" %%c IN (`docker run -d -p %PORT%:8000 %IMAGE_NAME%`) DO SET CONTAINER_ID=%%c

timeout /T 5 /NOBREAK >nul

echo [INFO] Iniciando cliente...
java -jar desktop_client/app/build/compose/jars/FLBTClient-windows-x64-1.0.0-release.jar

echo [INFO] Cliente fechado, parando container...
docker stop %CONTAINER_ID%

ENDLOCAL