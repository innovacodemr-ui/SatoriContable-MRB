#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Ejecutar migraciones automáticas al desplegar
echo "Running migrations..."
python manage.py migrate

echo "Configuring Site and SocialApp..."
python manage.py shell < scripts/ensure_site_config.py

# Recolectar estáticos (aunque ya se hace en build, no está de más o si se usan volumenes)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Arrancar el comando principal (Gunicorn)
exec "$@"
