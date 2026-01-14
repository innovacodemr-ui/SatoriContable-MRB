Write-Host " -> Agregando variables de entorno al servidor para correo..."

# Leer variables actuales si existen
$ServerIP = "178.156.215.106"
$EnvFile = "backend/.env"

# Agregar configuracion de correo al final
$EmailConfig = "
# Configuración Recepción de Facturas (Email Reader)
RECEPTION_EMAIL_HOST=imap.gmail.com
RECEPTION_EMAIL_PORT=993
RECEPTION_EMAIL_USER=tu_correo_recepcion@gmail.com
RECEPTION_EMAIL_PASSWORD=tu_contrasena_app
"

Add-Content $EnvFile $EmailConfig

# Desplegar
.\deploy_via_scp.ps1
