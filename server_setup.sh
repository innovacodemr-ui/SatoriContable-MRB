#!/bin/bash

# Satori ERP - Script de Instalación en Servidor (Ubuntu/Debian)
# Ejecutar como root o con sudo

echo "--- INICIANDO PROTOCOLO DE DESPLIEGUE SATORI ---"

# 1. Actualizar Sistema
echo "[1/5] Actualizando repositorios..."
apt-get update && apt-get upgrade -y
apt-get install -y curl git ufw

# 2. Instalar Docker y Docker Compose
if ! command -v docker &> /dev/null
then
    echo "[2/5] Instalando Docker..."
    apt-get install -y docker.io
    systemctl start docker
    systemctl enable docker
else
    echo "[2/5] Docker ya está instalado."
fi

if ! command -v docker-compose &> /dev/null
then
    echo "[3/5] Instalando Docker Compose..."
    apt-get install -y docker-compose
else
    echo "[3/5] Docker Compose ya está instalado."
fi

# 3. Configurar Firewall Básico
echo "[4/5] Configurando Firewall (UFW)..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# ufw enable # Comentado para evitar bloqueo accidental si no estás por SSH

# 4. Instrucciones Finales
echo "--- SERVIDOR PREPARADO ---"
echo "Para desplegar:"
echo "1. git clone https://github.com/innovacodemr-ui/SatoriContable-MRB.git satori"
echo "2. cd satori"
echo "3. Crea tu archivo .env"
echo "4. docker-compose -f docker-compose.prod.yml up -d --build"
