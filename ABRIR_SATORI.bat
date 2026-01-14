@echo off
echo ========================================
echo    INICIANDO SATORI - SISTEMA CONTABLE
echo ========================================
echo.
cd /d "%~dp0desktop"
echo Abriendo aplicacion de escritorio...
echo.
start cmd /k "npm start"
echo.
echo La aplicacion se abrira en unos segundos...
echo Puedes cerrar esta ventana.
echo.
timeout /t 3
exit
