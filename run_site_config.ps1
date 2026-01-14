$ServerIP = "178.156.215.106"
$User = "root"

Write-Host " -> Configuring Django Site..."

# Let's scp it.
scp fix_sso_remote.py ${User}@${ServerIP}:/root/satori/fix_sso_remote.py

if ($LASTEXITCODE -eq 0) {
    ssh ${User}@${ServerIP} "cd /root/satori && docker compose exec -T backend python manage.py shell < fix_sso_remote.py && rm fix_sso_remote.py"
}
else {
    Write-Error "SCP failed"
}
