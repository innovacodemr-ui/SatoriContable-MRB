$ServerIP = "178.156.215.106"
$User = "root"
$RemotePath = "/root/satori"

Write-Host " -> Starting SSO Configuration on Hetzner..."

# 1. Update .env with Google Keys
# We use a simple append strategy, assuming duplicates are handled by taking the last one or we accept redundancy for now.
# Better: Check if exists.
$EnvUpdateCmd = "
cd $RemotePath/backend
if ! grep -q 'GOOGLE_CLIENT_ID' .env; then
  echo '' >> .env
  echo 'GOOGLE_CLIENT_ID=__GOOGLE_CLIENT_ID__' >> .env
  echo 'GOOGLE_SECRET=__GOOGLE_SECRET__' >> .env
  echo 'Added Google Keys to .env'
else
  # Simple replacement if sed is available, or just warn.
  # For safety in this critical mission, we append overrides at the end which usually take precedence in many dotenv parsers,
  # OR we relies on the python script using the hardcoded values if env var is missing/old.
  # The python script I wrote defaults to the keys I have.
  echo 'Google Keys might already exist. Appending overrides...'
  echo 'GOOGLE_CLIENT_ID=__GOOGLE_CLIENT_ID__' >> .env
  echo 'GOOGLE_SECRET=__GOOGLE_SECRET__' >> .env
fi
"

$EnvUpdateCmd = $EnvUpdateCmd -replace "`r", ""

Write-Host " -> Updating .env..."
ssh ${User}@${ServerIP} $EnvUpdateCmd

# 2. Copy setup python script
Write-Host " -> Copying setup script..."
scp setup_sso_db.py ${User}@${ServerIP}:${RemotePath}/setup_sso_db.py

# 3. Exec setup script and Restart
$RemoteAction = "
cd $RemotePath
# Execute DB setup inside container
# We use cat and pipe to avoid shell redirection ambiguity across SSH
cat setup_sso_db.py | docker compose exec -T backend python manage.py shell
rm setup_sso_db.py

# Restart to pick up any changes
echo 'Restarting containers...'
docker compose restart backend
"

$RemoteAction = $RemoteAction -replace "`r", ""

ssh ${User}@${ServerIP} $RemoteAction

if ($LASTEXITCODE -eq 0) {
  Write-Host " [OK] SSO Configuration Completed Successfully."
}
else {
  Write-Error " [ERROR] SSO Configuration Failed."
}
