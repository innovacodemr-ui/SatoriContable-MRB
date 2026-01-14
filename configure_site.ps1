$ServerIP = "178.156.215.106"
$User = "root"

# Use distinct variable for inner quotes to avoid escaping hell
$Cmd = "from django.contrib.sites.models import Site; s=Site.objects.get(id=1); s.domain='innovacode-mrb.com'; s.name='Satori MRB'; s.save(); print('Site Updated:', s.domain)"

$RemoteScript = @"
cd /root/satori
docker compose exec -T backend python manage.py shell -c "${Cmd}"
"@

# Remove Windows CR
$RemoteScript = $RemoteScript -replace "`r", ""

ssh ${User}@${ServerIP} $RemoteScript