#!/bin/bash

# Stop execution on error
set -e

echo "🚀 Iniciando despliegue de Satori en Producción..."

# 1. Pull de cambios
echo "📥 Descargando últimos cambios del repositorio..."
git pull origin main

# 2. Construir y levantar contenedores
echo "🐳 Construyendo y levantando contenedores..."
# Usar --build para asegurar que se regeneren las imágenes con los cambios recientes
docker compose up -d --build

# 3. Limpieza (Opcional)
echo "🧹 Limpiando imágenes antiguas..."
docker image prune -f

echo "✅ Despliegue completado exitosamente."
echo "🌐 Backend activo en puerto 8000"
echo "🌐 Frontend activo en puerto 3000 (o 80 vía Nginx)"
