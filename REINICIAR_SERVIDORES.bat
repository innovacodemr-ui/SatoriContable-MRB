@echo off
setlocal enabledelayedexpansion
TITLE Satori - Reiniciar Servicios
cd /d "%~dp0"
set "BASE_DIR=%~dp0"

echo ===============================================
echo      REINICIANDO SERVIDORES DE SATORI
echo      Ruta Base: "!BASE_DIR!"
echo ===============================================
echo.

echo [1/3] Deteniendo servicios anteriores...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo.
echo [2/3] Iniciando Backend...
if exist "%BASE_DIR%.venv\Scripts\python.exe" (
    start "Satori Backend" cmd /k "cd /d "!BASE_DIR!backend" && "!BASE_DIR!.venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000"
) else (
    echo [ERROR] No se encuentra el entorno virtual Python en .venv\Scripts\python.exe
    pause
)

echo.
echo [3/3] Iniciando Frontend...
if exist "%BASE_DIR%frontend" (
    start "Satori Frontend" cmd /k "cd /d "!BASE_DIR!frontend" && npm run dev"
) else (
    echo [ERROR] No se encuentra la carpeta frontend
    pause
)

echo.
echo ===============================================
echo      LISTO!
echo ===============================================
timeout /t 5

