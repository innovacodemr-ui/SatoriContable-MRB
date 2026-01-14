# Guía de Inicio Rápido - Satori

## 🚀 Inicio Rápido con Docker

La forma más rápida de empezar es usando Docker:

### 1. Configurar Variables de Entorno

```bash
cp backend/.env.example backend/.env
```

Edita `backend/.env` y configura:
- `SECRET_KEY`: Genera una clave secura
- `DATABASE_URL`: Deja el valor por defecto para Docker
- `DIAN_*`: Configura tus credenciales DIAN

### 2. Iniciar Servicios

```bash
docker-compose up -d
```

Esto iniciará:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Backend Django (puerto 8000)
- Frontend React (puerto 3000)
- Celery Worker
- Celery Beat

### 3. Ejecutar Migraciones

```bash
docker-compose exec backend python manage.py migrate_schemas --shared
```

### 4. Crear Superusuario

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 5. Acceder a la Aplicación

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Django**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs/

## 🖥️ Instalación Manual (Desarrollo)

### Requisitos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# Editar .env con tus configuraciones

# Crear base de datos (en PostgreSQL)
psql -U postgres
CREATE DATABASE satori_db;
CREATE USER satori_user WITH PASSWORD 'satori_pass';
GRANT ALL PRIVILEGES ON DATABASE satori_db TO satori_user;
\q

# Ejecutar migraciones
python manage.py migrate_schemas --shared
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Celery (Opcional para desarrollo)

En terminales separadas:

```bash
# Worker
cd backend
celery -A config worker -l info

# Beat
celery -A config beat -l info
```

## 📋 Primeros Pasos

### 1. Crear tu Primera Empresa (Tenant)

1. Accede al admin: http://localhost:8000/admin
2. Ve a "Clientes/Empresas"
3. Crea un nuevo cliente con:
   - **Schema name**: `empresa1` (único, sin espacios)
   - **Name**: Nombre de tu empresa
   - **NIT**: NIT de la empresa
   - **Legal name**: Razón social
   - **Tax regime**: Régimen tributario
   - Completa la información de contacto

4. En "Dominios", crea un dominio:
   - **Domain**: `empresa1.localhost`
   - **Tenant**: Selecciona la empresa creada
   - **Is primary**: ✓

### 2. Ejecutar Migraciones del Tenant

```bash
python manage.py migrate_schemas --tenant=empresa1
```

### 3. Configurar el Plan de Cuentas (PUC)

El sistema incluye el PUC colombiano. Puedes:

1. Importar el PUC completo (crear un comando de management)
2. Crear cuentas manualmente desde el admin
3. Usar la API para crear cuentas

Ejemplo de cuentas básicas:

```python
# Activos
1 - Activo (Clase)
11 - Disponible (Grupo)
1105 - Caja (Cuenta)
110505 - Caja General (Subcuenta)

# Pasivos
2 - Pasivo (Clase)
24 - Impuestos, gravámenes y tasas (Grupo)
2408 - IVA por pagar (Cuenta)

# Patrimonio
3 - Patrimonio (Clase)
31 - Capital Social (Grupo)

# Ingresos
4 - Ingresos (Clase)
41 - Operacionales (Grupo)

# Gastos
5 - Gastos (Clase)
51 - Operacionales de administración (Grupo)
```

### 4. Crear Terceros (Clientes/Proveedores)

1. Ve a "Terceros" en el admin o la aplicación web
2. Crea clientes y proveedores con:
   - Tipo de identificación
   - Número de identificación
   - Información de contacto
   - Régimen tributario

### 5. Configurar Resolución DIAN

Para facturación electrónica:

1. Ve a "Resoluciones DIAN"
2. Crea una resolución con:
   - Número de resolución
   - Prefijo de facturación
   - Rango de numeración (desde-hasta)
   - Fecha de vigencia
   - Clave técnica (si aplica)

### 6. Crear tu Primera Factura

1. Ve a "Documentos Electrónicos"
2. Crea una nueva factura:
   - Selecciona cliente
   - Agrega líneas de productos/servicios
   - El sistema calcula IVA automáticamente
3. Envía a DIAN (requiere configuración DIAN)

## 🔧 Configuración DIAN

Para habilitar la facturación electrónica:

### 1. Obtener Certificado Digital

- Adquiere un certificado digital (.p12) de una entidad certificadora
- Guarda el certificado en un lugar seguro
- Anota la contraseña del certificado

### 2. Registrar Software en DIAN

- Regístrate en el portal DIAN
- Obtén tu Software ID y PIN
- Completa el proceso de habilitación

### 3. Configurar en Satori

En `backend/.env`:

```env
DIAN_TEST_MODE=True  # False en producción
DIAN_SOFTWARE_ID=tu-software-id
DIAN_SOFTWARE_PIN=tu-software-pin
DIAN_CERTIFICATE_PATH=/ruta/a/certificado.p12
DIAN_CERTIFICATE_PASSWORD=contraseña-certificado
DIAN_NIT=tu-nit
```

## 📊 Generación de Reportes

### Balance General

```
GET /api/accounting/balance-sheet/?date=2024-01-31
```

### Estado de Resultados

```
GET /api/accounting/income-statement/?from=2024-01-01&to=2024-12-31
```

### Balance de Comprobación

```
GET /api/accounting/trial-balance/?date=2024-01-31
```

## 🔄 Sincronización Desktop

La aplicación desktop (próximamente) permitirá:

1. Trabajar offline con SQLite local
2. Sincronización automática al conectarse
3. Resolución de conflictos
4. Cola de cambios pendientes

## 🆘 Solución de Problemas

### Puerto 8000 ya está en uso

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Error de permisos en PostgreSQL

```sql
GRANT ALL PRIVILEGES ON DATABASE satori_db TO satori_user;
GRANT ALL ON SCHEMA public TO satori_user;
```

### Celery no inicia

Verificar que Redis esté corriendo:

```bash
redis-cli ping
# Debe responder: PONG
```

### Error en migraciones multi-tenant

Primero ejecutar las migraciones shared:

```bash
python manage.py migrate_schemas --shared
```

Luego las del tenant:

```bash
python manage.py migrate_schemas --tenant=empresa1
```

## 📚 Recursos Adicionales

- [Documentación Técnica](docs/TECHNICAL.md)
- [Documentación DIAN](https://www.dian.gov.co/factura-electronica)
- [PUC Colombia](https://www.ctcp.gov.co/)

## 🎯 Próximos Pasos

1. Explorar el módulo de contabilidad
2. Crear comprobantes contables
3. Configurar facturación electrónica
4. Generar reportes contables
5. Personalizar el plan de cuentas

¡Bienvenido a Satori! 🚀
