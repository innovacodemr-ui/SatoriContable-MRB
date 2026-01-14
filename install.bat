@echo off
REM Script de instalación para Satori - Sistema Contable
REM Para Windows

echo ======================================
echo Satori - Sistema Contable
echo Instalacion y Configuracion
echo ======================================

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Python no esta instalado
    exit /b 1
)
echo + Python encontrado

REM Verificar Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo X Node.js no esta instalado
    exit /b 1
)
echo + Node.js encontrado

REM Backend Setup
echo.
echo Configurando Backend...
cd backend

REM Crear entorno virtual
python -m venv venv
call venv\Scripts\activate.bat

REM Instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Copiar archivo de entorno
if not exist .env (
    copy .env.example .env
    echo ! Configura backend\.env con tus credenciales
)

REM Crear directorios necesarios
if not exist logs mkdir logs
if not exist media mkdir media
if not exist staticfiles mkdir staticfiles

cd ..

REM Frontend Setup
echo.
echo Configurando Frontend...
cd frontend

call npm install

cd ..

echo.
echo ======================================
echo + Instalacion completada
echo ======================================
echo.
echo Proximos pasos:
echo 1. Configura backend\.env con tus credenciales
echo 2. Crea la base de datos PostgreSQL
echo 3. Ejecuta: cd backend ^&^& python manage.py migrate_schemas --shared
echo 4. Ejecuta: python manage.py createsuperuser
echo 5. Inicia el backend: python manage.py runserver
echo 6. En otra terminal, inicia el frontend: cd frontend ^&^& npm run dev
echo.

pause
