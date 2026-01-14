Write-Host " -> Iniciando proceso de despliegue a Hetzner (Sin Git)..."

$ServerIP = "178.156.215.106"
$User = "root"
$RemotePath = "/root/satori"

# 1. Empaquetar
Write-Host " -> Creando archivo comprimido (deploy.tar.gz)..."
# Usamos tar si está disponible (Windows 10/11)
try {
    tar --exclude='node_modules' --exclude='.venv' --exclude='__pycache__' --exclude='.git' --exclude='db.sqlite3' -czf deploy.tar.gz backend frontend docker-compose.yml backend/.env deploy.sh
} catch {
    Write-Error "Error ejecutando tar via PowerShell. Asegúrate de tener tar instalado o usa WSL."
    exit 1
}

# 2. Enviar
Write-Host " -> Enviando archivos al servidor..."
scp deploy.tar.gz ${User}@${ServerIP}:${RemotePath}/deploy.tar.gz

if ($LASTEXITCODE -ne 0) {
    Write-Error " [ERROR] Fallo la copia de archivos. Verifica tu conexion SSH."
    exit 1
}

# 3. Ejecutar comandos remotos
Write-Host " -> Ejecutando despliegue en el servidor..."
$RemoteCommands = "
    mkdir -p ${RemotePath}
    cd ${RemotePath}
    tar -xzf deploy.tar.gz
    chmod +x deploy.sh
    
    echo 'Building images...'
    # Intentamos construir primero sin detener el servicio
    if docker compose build || docker-compose build; then
        echo 'Build successful. Restarting services...'
        docker compose down || docker-compose down
        docker compose up -d || docker-compose up -d
        docker image prune -f
    else
        echo 'CRITICAL: Build failed! Services were NOT restarted to avoid downtime (if they were running).'
        echo 'Check the build logs above for errors.'
        exit 1
    fi
"
# Eliminar Retorno de Carro de Windows para evitar errores en Bash
$RemoteCommands = $RemoteCommands -replace "`r", ""

ssh ${User}@${ServerIP} $RemoteCommands

if ($LASTEXITCODE -eq 0) {
    Write-Host " [OK] Despliegue completado con exito."
    Write-Host "   Backend disponible en: http://178.156.215.106:8000"
    Write-Host "   Frontend disponible en: http://178.156.215.106"
} else {
    Write-Error " [ERROR] Hubo un error ejecutando los comandos remotos."
}
