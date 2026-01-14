# Comandos Útiles - Sistema Satori

## 🚀 Comandos de Inicio

### Activar Entorno Virtual

**Windows:**
```bash
cd backend
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd backend
source venv/bin/activate
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

## 📊 Comandos de Base de Datos

### Migraciones Multi-tenant

**Crear migraciones:**
```bash
python manage.py makemigrations
```

**Migrar schema compartido (public):**
```bash
python manage.py migrate_schemas --shared
```

**Migrar tenant específico:**
```bash
python manage.py migrate_schemas --tenant=empresa1
```

**Migrar todos los tenants:**
```bash
python manage.py migrate_schemas
```

### Crear Superusuario

```bash
python manage.py createsuperuser
```

### Crear Tenant desde CLI

```bash
python manage.py shell
```

Luego en el shell:
```python
from apps.tenants.models import Client, Domain

# Crear cliente
client = Client.objects.create(
    schema_name='empresa1',
    name='Mi Empresa S.A.S',
    nit='900123456-1',
    legal_name='MI EMPRESA S.A.S',
    tax_regime='COMUN',
    address='Calle 123 #45-67',
    city='Cali',
    department='Valle del Cauca',
    phone='3001234567',
    email='info@miempresa.com'
)

# Crear dominio
Domain.objects.create(
    domain='empresa1.localhost',
    tenant=client,
    is_primary=True
)

print(f"Tenant creado: {client.schema_name}")
```

Migrar el nuevo tenant:
```bash
python manage.py migrate_schemas --tenant=empresa1
```

## 🖥️ Comandos del Servidor

### Servidor de Desarrollo

```bash
python manage.py runserver
# o especificar puerto
python manage.py runserver 8000
```

### Shell Interactivo

```bash
python manage.py shell
```

### DBShell

```bash
python manage.py dbshell
```

## 🔄 Comandos de Celery

### Iniciar Worker

**Windows:**
```bash
celery -A config worker -l info --pool=solo
```

**Linux/Mac:**
```bash
celery -A config worker -l info
```

### Iniciar Beat (Tareas Programadas)

```bash
celery -A config beat -l info
```

### Ver Tareas Activas

```bash
celery -A config inspect active
```

### Purgar Cola de Tareas

```bash
celery -A config purge
```

## 📦 Comandos de Gestión de Datos

### Dump Data

**Exportar datos de un tenant:**
```bash
python manage.py dumpdata --schema=empresa1 > empresa1_backup.json
```

**Exportar datos compartidos:**
```bash
python manage.py dumpdata tenants --natural-foreign --natural-primary > tenants_backup.json
```

### Load Data

```bash
python manage.py loaddata tenants_backup.json
```

### Crear Fixtures del PUC

Crear archivo `backend/apps/accounting/fixtures/puc_inicial.json`:

```json
[
  {
    "model": "accounting.accountclass",
    "pk": 1,
    "fields": {
      "code": "1",
      "name": "Activo",
      "nature": "DEBITO",
      "is_active": true
    }
  },
  {
    "model": "accounting.accountclass",
    "pk": 2,
    "fields": {
      "code": "2",
      "name": "Pasivo",
      "nature": "CREDITO",
      "is_active": true
    }
  }
]
```

Cargar fixtures:
```bash
python manage.py loaddata puc_inicial
```

## 🧹 Comandos de Limpieza

### Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### Limpiar Sesiones Expiradas

```bash
python manage.py clearsessions
```

### Limpiar Caché

```bash
python manage.py shell
```

```python
from django.core.cache import cache
cache.clear()
```

## 🔍 Comandos de Inspección

### Listar Tenants

```bash
python manage.py shell
```

```python
from apps.tenants.models import Client
for client in Client.objects.all():
    print(f"{client.schema_name} - {client.name} - {client.nit}")
```

### Ver Estructura de BD

```bash
python manage.py showmigrations
```

### Verificar Configuración

```bash
python manage.py check
python manage.py check --deploy  # Checklist para producción
```

## 📊 Comandos Personalizados

### Crear Comando Personalizado

Crear archivo `backend/apps/accounting/management/commands/import_puc.py`:

```python
from django.core.management.base import BaseCommand
from apps.accounting.models import Account

class Command(BaseCommand):
    help = 'Importa el Plan Único de Cuentas'

    def handle(self, *args, **options):
        self.stdout.write('Importando PUC...')
        
        # Lógica de importación aquí
        
        self.stdout.write(self.style.SUCCESS('PUC importado exitosamente'))
```

Ejecutar:
```bash
python manage.py import_puc
```

### Ejemplo: Crear Datos de Prueba

```bash
python manage.py shell
```

```python
from apps.accounting.models import ThirdParty

# Crear cliente de prueba
cliente = ThirdParty.objects.create(
    party_type='CLIENTE',
    person_type='JURIDICA',
    id_type='NIT',
    id_number='900123456',
    verification_digit='1',
    business_name='Cliente Test S.A.S',
    tax_regime='COMUN',
    address='Calle 123',
    city='Cali',
    department='Valle del Cauca',
    email='cliente@test.com',
    is_active=True
)

print(f"Cliente creado: {cliente}")
```

## 🐳 Comandos Docker

### Construir e Iniciar

```bash
docker-compose up -d --build
```

### Ver Logs

```bash
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### Ejecutar Comando en Container

```bash
docker-compose exec backend python manage.py migrate_schemas --shared
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py shell
```

### Reiniciar Servicios

```bash
docker-compose restart backend
docker-compose restart celery_worker
```

### Detener Servicios

```bash
docker-compose down
# Con volúmenes
docker-compose down -v
```

### Ver Estado

```bash
docker-compose ps
```

## 🧪 Comandos de Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests de una app
python manage.py test apps.accounting

# Test específico
python manage.py test apps.accounting.tests.test_models

# Con coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Crear Tests

Crear archivo `backend/apps/accounting/tests/test_models.py`:

```python
from django.test import TestCase
from apps.accounting.models import Account

class AccountTestCase(TestCase):
    def setUp(self):
        Account.objects.create(
            code='1105',
            name='Caja',
            nature='DEBITO'
        )
    
    def test_account_creation(self):
        account = Account.objects.get(code='1105')
        self.assertEqual(account.name, 'Caja')
```

## 🔧 Comandos de Debugging

### Shell Plus (con django-extensions)

```bash
pip install django-extensions ipython
```

En settings.py:
```python
INSTALLED_APPS += ['django_extensions']
```

Ejecutar:
```bash
python manage.py shell_plus
```

### Ver SQL de Queries

```bash
python manage.py shell
```

```python
from django.db import connection
from apps.accounting.models import Account

accounts = Account.objects.all()
print(connection.queries)
```

### Debug Toolbar (Desarrollo)

En settings.py:
```python
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

## 📝 Comandos de Producción

### Crear Backup

```bash
# PostgreSQL
pg_dump -h localhost -U satori_user -d satori_db > backup_$(date +%Y%m%d).sql

# Django dumpdata
python manage.py dumpdata --natural-foreign --natural-primary > full_backup.json
```

### Restaurar Backup

```bash
# PostgreSQL
psql -h localhost -U satori_user -d satori_db < backup_20240101.sql

# Django loaddata
python manage.py loaddata full_backup.json
```

### Verificar para Producción

```bash
python manage.py check --deploy
```

### Recolectar Estáticos para Producción

```bash
python manage.py collectstatic --noinput --clear
```

## 🔑 Variables de Entorno Útiles

```bash
# Development
export DEBUG=True
export DJANGO_SETTINGS_MODULE=config.settings

# Production
export DEBUG=False
export SECRET_KEY=your-super-secret-key
export DATABASE_URL=postgresql://user:pass@host:port/db
```

## 📊 Comandos de Análisis

### Ver Modelos

```bash
python manage.py inspectdb
```

### Estadísticas de DB

```bash
python manage.py shell
```

```python
from apps.accounting.models import Account, JournalEntry
from apps.tenants.models import Client

print(f"Tenants: {Client.objects.count()}")
print(f"Cuentas: {Account.objects.count()}")
print(f"Comprobantes: {JournalEntry.objects.count()}")
```

## 🎯 Atajos Útiles

### Crear Alias (Linux/Mac)

En `~/.bashrc` o `~/.zshrc`:

```bash
alias satori-server='cd ~/satori/backend && source venv/bin/activate && python manage.py runserver'
alias satori-celery='cd ~/satori/backend && source venv/bin/activate && celery -A config worker -l info'
alias satori-shell='cd ~/satori/backend && source venv/bin/activate && python manage.py shell'
```

### Crear Script de Inicio (Windows)

Crear `start_satori.bat`:

```batch
@echo off
cd backend
call venv\Scripts\activate.bat
start cmd /k "python manage.py runserver"
start cmd /k "celery -A config worker -l info --pool=solo"
cd ../frontend
start cmd /k "npm run dev"
```

---

## 📚 Referencias

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Tenants](https://django-tenants.readthedocs.io/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)

---

**Nota**: Estos comandos asumen que estás en el directorio raíz del proyecto o en el directorio backend según corresponda.
