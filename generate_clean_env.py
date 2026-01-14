import os

content = """SECRET_KEY=django-insecure-prod-key-change-me
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,backend,178.156.215.106
DATABASE_URL=postgres://postgres:Mario@localhost:5432/satori_db
DB_NAME=satori_db
DB_USER=postgres
DB_PASSWORD=Mario
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://178.156.215.106
DIAN_ENV=PRODUCTION
DIAN_TEST_MODE=False
RECEPTION_EMAIL_HOST=imap.gmail.com
RECEPTION_EMAIL_PORT=993
RECEPTION_EMAIL_USER=gerenciaonce1@gmail.com
RECEPTION_EMAIL_PASSWORD=exrqepxodwyrgjnl
ENCRYPTION_KEY=l5t4JliXKNnB7LR8D3o7ZB7eFhkqgYLDSk-UuVq9chc=
GOOGLE_CLIENT_ID=__GOOGLE_CLIENT_ID__
GOOGLE_SECRET=__GOOGLE_SECRET__
"""

# Write binary to ensure no BOM and force \n
with open('backend/.env.clean', 'wb') as f:
    f.write(content.replace('\r\n', '\n').encode('utf-8'))

print("Clean .env created.")
