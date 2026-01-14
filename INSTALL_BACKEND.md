# 🚀 Guía Rápida de Instalación - Backend Django

## ⚠️ Pre-requisitos

El backend requiere:
- **Python 3.10+** o **Docker Desktop**

## Opción 1: Con Docker (Recomendado)

### Instalar Docker Desktop

1. Descargar de: https://www.docker.com/products/docker-desktop/
2. Instalar Docker Desktop para Windows
3. Reiniciar el sistema si es necesario
4. Verificar instalación:
   ```bash
   docker --version
   docker-compose --version
   ```

### Levantar Backend

```bash
cd backend
docker-compose up -d
```

Esto levantará:
- PostgreSQL en puerto 5432
- Redis en puerto 6379
- Django en puerto 8000
- Celery workers

### Aplicar Migraciones

```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
```

### Acceder

- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- Docs: http://localhost:8000/api/schema/swagger-ui/

## Opción 2: Instalación Manual Python

### Instalar Python

1. Descargar Python 3.10+ de: https://www.python.org/downloads/
2. Durante instalación marcar "Add Python to PATH"
3. Verificar:
   ```bash
   python --version
   pip --version
   ```

### Configurar Entorno Virtual

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Configurar Base de Datos

Para desarrollo rápido, usar SQLite (ya configurado en settings_dev.py):

```bash
# Usar settings de desarrollo
set DJANGO_SETTINGS_MODULE=config.settings_dev

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### Iniciar Servidor

```bash
python manage.py runserver
```

El servidor estará en http://localhost:8000

## Opción 3: Solo Desktop (Sin Backend)

**✅ Ya funciona actualmente**

La aplicación desktop usa SQLite local y no requiere backend para funcionar.
Puedes trabajar 100% offline.

### Características Desktop

- Base de datos SQLite local
- Todas las funcionalidades disponibles
- Trabajo offline completo
- Sincronización cuando haya backend

## 🔧 Configuración del Frontend

El frontend detecta automáticamente si hay backend disponible:

```bash
cd frontend

# Crear archivo .env
echo VITE_API_URL=http://localhost:8000/api > .env

# Iniciar frontend
npm run dev
```

## 🧪 Probar Integración

### 1. Modo Desktop (Sin Backend)
```bash
cd desktop
npm start
```
✅ Funciona inmediatamente con SQLite

### 2. Modo Web (Con Backend)
```bash
# Terminal 1 - Backend
cd backend
python manage.py runserver

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Acceder a http://localhost:3001

## 📊 Verificar Estado

### Desktop
- Base de datos: `%APPDATA%\satori-desktop\satori.db`
- Logs: En consola de Electron (Ctrl+Shift+I)

### Backend
- Health check: http://localhost:8000/api/health/
- Admin: http://localhost:8000/admin/
- API docs: http://localhost:8000/api/schema/swagger-ui/

## 🆘 Solución de Problemas

### Python no encontrado
- Reinstalar Python marcando "Add to PATH"
- O usar Microsoft Store: `python3`

### Docker no inicia
- Verificar que WSL2 esté instalado (Windows)
- Verificar que Docker Desktop esté corriendo
- Revisar logs en Docker Desktop

### Puerto 8000 ocupado
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Error de migraciones
```bash
python manage.py migrate --run-syncdb
```

## 📚 Documentación Adicional

- [README.md](../README.md) - Documentación completa
- [QUICKSTART.md](../docs/QUICKSTART.md) - Guía de inicio
- [TECHNICAL.md](../docs/TECHNICAL.md) - Documentación técnica

## ✅ Estado Actual

**Sin Backend (Desktop Only)**:
- ✅ SQLite local funcionando
- ✅ Todas las páginas implementadas
- ✅ CRUD completo de cuentas, terceros, comprobantes
- ✅ Trabajo offline

**Con Backend** (cuando se instale):
- ✅ API REST completa
- ✅ PostgreSQL multi-tenant
- ✅ Sincronización desktop ↔ web
- ✅ Múltiples empresas
- ✅ Integración DIAN (por implementar)

## 🎯 Recomendación

Para empezar, usa **Modo Desktop** que ya funciona.

Instala el backend cuando necesites:
- Trabajar desde navegador web
- Sincronización entre dispositivos
- Múltiples usuarios
- Múltiples empresas (multi-tenant)
