@echo off
SETLOCAL

:: Nome da imagem
SET IMAGE_NAME=backingtracker_server

:: Porta da API
SET PORT=8000

:: Verifica se a imagem já existe
docker image inspect %IMAGE_NAME% >nul 2>&1
IF ERRORLEVEL 1 (
    echo [INFO] Criando imagem Docker...
    docker build -t %IMAGE_NAME% server
)

echo [INFO] Iniciando servidor backend...
start /B docker run --rm -p %PORT%:8000 %IMAGE_NAME%

:: Aguarda o backend subir (básico, 5s)
timeout /T 5 /NOBREAK >nul

echo [INFO] Iniciando cliente...
start javaw -jar desktop_client/app/build/compose/jars/FLBTClient-windows-x64-1.0.0-release.jar

ENDLOCAL