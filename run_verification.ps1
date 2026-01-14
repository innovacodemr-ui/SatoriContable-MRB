$ServerIP = "178.156.215.106"
$User = "root"
$RemotePath = "/root/satori"

scp verify_sso_config.py ${User}@${ServerIP}:${RemotePath}/verify_sso_config.py

$VerifyCmd = "
cd $RemotePath
cat verify_sso_config.py | docker compose exec -T backend python manage.py shell
rm verify_sso_config.py
"

$VerifyCmd = $VerifyCmd -replace "`r", ""

ssh ${User}@${ServerIP} $VerifyCmd
