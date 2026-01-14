-- Script SQL para crear la base de datos y el usuario
-- PostgreSQL

-- Crear usuario
CREATE USER satori_user WITH PASSWORD 'satori_pass';

-- Crear base de datos
CREATE DATABASE satori_db
    WITH 
    OWNER = satori_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'es_CO.UTF-8'
    LC_CTYPE = 'es_CO.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Otorgar privilegios
GRANT ALL PRIVILEGES ON DATABASE satori_db TO satori_user;

-- Conectar a la base de datos
\c satori_db

-- Otorgar privilegios en el schema public
GRANT ALL ON SCHEMA public TO satori_user;

-- Comentarios
COMMENT ON DATABASE satori_db IS 'Base de datos del Sistema Contable Satori';

-- Nota: Después de crear la base de datos, ejecutar:
-- python manage.py migrate_schemas --shared
-- python manage.py createsuperuser
