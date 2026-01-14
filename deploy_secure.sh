#!/bin/bash
# ===================================================================
# SCRIPT DE DEPLOYMENT SEGURO - SATORI
# ===================================================================
# Este script realiza el deployment con las mejores prácticas de seguridad
# ===================================================================

set -e  # Detener en caso de error

SERVER_IP="178.156.215.106"
SERVER_USER="root"
REMOTE_PATH="/root/satori"

echo "🔒 DEPLOYMENT SEGURO - SATORI"
echo "================================"

# 1. Verificar que existe .env.production.template localmente
if [ ! -f ".env.production.template" ]; then
    echo "❌ ERROR: No se encuentra .env.production.template"
    exit 1
fi

# 2. Verificar que el archivo .env existe en el servidor
echo "📋 Verificando configuración en servidor..."
ssh ${SERVER_USER}@${SERVER_IP} "
    if [ ! -f ${REMOTE_PATH}/.env ]; then
        echo '❌ ERROR: No existe ${REMOTE_PATH}/.env en el servidor'
        echo 'Por favor:'
        echo '1. Copiar .env.production.template al servidor'
        echo '2. Renombrar a .env'
        echo '3. Editar y completar TODOS los valores <CAMBIAR>'
        echo '4. Ejecutar: chmod 600 ${REMOTE_PATH}/.env'
        exit 1
    fi
    
    echo '✅ Archivo .env encontrado'
    
    # Verificar permisos
    PERMS=\$(stat -c '%a' ${REMOTE_PATH}/.env)
    if [ \"\$PERMS\" != \"600\" ]; then
        echo '⚠️  Corrigiendo permisos del .env a 600'
        chmod 600 ${REMOTE_PATH}/.env
    fi
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 3. Crear el tarball excluyendo archivos sensibles
echo "📦 Empaquetando código..."
tar --exclude='node_modules' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='db.sqlite3' \
    --exclude='.env*' \
    --exclude='*.pyc' \
    -czf deploy.tar.gz backend frontend docker-compose.yml

# 4. Enviar al servidor
echo "🚀 Enviando al servidor..."
scp deploy.tar.gz ${SERVER_USER}@${SERVER_IP}:${REMOTE_PATH}/deploy.tar.gz

# 5. Desplegar en el servidor
echo "🔧 Desplegando en servidor..."
ssh ${SERVER_USER}@${SERVER_IP} "
    cd ${REMOTE_PATH}
    
    # Extraer
    tar -xzf deploy.tar.gz
    
    # Build y restart con el .env
    echo '🔨 Construyendo imágenes...'
    docker compose build
    
    echo '♻️  Reiniciando servicios...'
    docker compose down
    docker compose --env-file .env up -d
    
    # Limpiar
    docker image prune -f
    rm deploy.tar.gz
    
    echo '✅ Deployment completado'
"

# 6. Limpiar local
rm deploy.tar.gz

echo ""
echo "✅ DEPLOYMENT COMPLETADO"
echo "================================"
echo "Backend: http://${SERVER_IP}:8000"
echo "Frontend: http://${SERVER_IP}"
echo ""
echo "⚠️  RECORDATORIO DE SEGURIDAD:"
echo "1. Verificar que .env en servidor tenga las nuevas credenciales de Google"
echo "2. Revocar las credenciales antiguas en Google Cloud Console"
echo "3. NUNCA subir el archivo .env al repositorio"
