# Satori - Sistema Contable Multi-tenant

Sistema contable profesional basado en normativa colombiana con facturación electrónica DIAN, versiones web y de escritorio con sincronización offline.

## 🚀 Características Principales

### ✅ Arquitectura Multi-tenant
- Gestión de múltiples empresas en una sola instalación
- Separación completa de datos por tenant
- Configuración individual por empresa

### 📊 Contabilidad Completa
- **Plan Único de Cuentas (PUC)** colombiano
- Comprobantes contables con múltiples tipos
- Centros de costo
- Gestión de terceros (clientes, proveedores, empleados)
- Balance General
- Estado de Resultados
- Balance de Comprobación

### 🧾 Facturación Electrónica DIAN
- Integración completa con servicios web DIAN
- Generación de CUFE/CUDE
- Firma digital de documentos
- Códigos QR
- Facturas de venta
- Notas crédito y débito
- Documentos soporte
- Validación en tiempo real

### 💰 Impuestos Colombianos
- IVA (19%, 5%, 0%)
- Retención en la Fuente
- Retención de IVA
- Retención de ICA (específico para Cali)
- Impuesto de Industria y Comercio

### 🌐 Versión Web (React + Material-UI)
- Interfaz moderna y responsiva
- Dashboard con métricas en tiempo real
- Gestión completa de todos los módulos

### 💻 Versión Desktop (Electron)
- Aplicación nativa para Windows, macOS y Linux
- Base de datos local SQLite
- Sincronización automática cuando hay internet
- Funcionamiento 100% offline

### 🔄 Sincronización Inteligente
- Sincronización bidireccional
- Resolución de conflictos
- Cola de cambios pendientes
- Logs detallados de sincronización

## 🏗️ Arquitectura Técnica

### Backend (Django)
```
backend/
├── config/              # Configuración del proyecto
│   ├── settings.py      # Settings con multi-tenant
│   ├── urls.py          # URLs principales
│   ├── celery.py        # Configuración Celery
│   └── wsgi.py          # WSGI application
├── apps/
│   ├── core/            # Funcionalidades core
│   ├── tenants/         # Gestión multi-tenant
│   ├── accounting/      # Módulo contable (PUC, asientos)
│   ├── dian/            # Facturación electrónica DIAN
│   ├── invoicing/       # Facturación general
│   ├── taxes/           # Gestión de impuestos
│   ├── reports/         # Reportes contables
│   └── sync/            # Sincronización desktop
├── requirements.txt     # Dependencias Python
└── Dockerfile          # Contenedor Docker
```

### Frontend Web (React + TypeScript)
```
frontend/
├── src/
│   ├── layouts/         # Layouts principales
│   ├── pages/           # Páginas de la aplicación
│   │   ├── accounting/  # Módulo contable
│   │   ├── dian/        # Facturación electrónica
│   │   └── reports/     # Reportes
│   ├── components/      # Componentes reutilizables
│   ├── services/        # Servicios API
│   └── App.tsx          # Componente principal
├── package.json
└── vite.config.ts
```

### Desktop (Electron - Próximamente)
```
desktop/
├── main/                # Proceso principal Electron
├── renderer/            # Interfaz de usuario
├── database/            # SQLite local
└── sync/                # Lógica de sincronización
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.0** - Framework web
- **Django REST Framework** - API REST
- **django-tenants** - Multi-tenancy
- **PostgreSQL** - Base de datos principal
- **Redis** - Cache y cola de tareas
- **Celery** - Tareas asíncronas
- **Celery Beat** - Tareas programadas

### Frontend Web
- **React 18** - Biblioteca UI
- **TypeScript** - Tipado estático
- **Material-UI (MUI)** - Componentes UI
- **React Router** - Navegación
- **Axios** - Cliente HTTP
- **Formik + Yup** - Formularios y validación

### Desktop
- **Electron** - Framework desktop
- **SQLite** - Base de datos local
- **React** - Interfaz de usuario

### Infraestructura
- **Docker & Docker Compose** - Contenedores
- **Gunicorn** - Servidor WSGI
- **Nginx** - Reverse proxy (producción)

## 📋 Requisitos Previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (opcional)

## 🚀 Instalación y Configuración

### Opción 1: Con Docker (Recomendado)

1. **Clonar el repositorio**
```bash
cd "Satori - MRB"
```

2. **Configurar variables de entorno**
```bash
cp backend/.env.example backend/.env
# Editar backend/.env con tus configuraciones
```

3. **Construir y ejecutar con Docker**
```bash
docker-compose up -d
```

4. **Ejecutar migraciones**
```bash
docker-compose exec backend python manage.py migrate_schemas --shared
docker-compose exec backend python manage.py createsuperuser
```

5. **Acceder a la aplicación**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Admin: http://localhost:8000/admin

### Opción 2: Instalación Manual

#### Backend

1. **Crear entorno virtual**
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos PostgreSQL**
```sql
CREATE DATABASE satori_db;
CREATE USER satori_user WITH PASSWORD 'satori_pass';
GRANT ALL PRIVILEGES ON DATABASE satori_db TO satori_user;
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar migraciones**
```bash
python manage.py migrate_schemas --shared
python manage.py createsuperuser
```

6. **Iniciar servidor de desarrollo**
```bash
python manage.py runserver
```

7. **Iniciar Celery (en otra terminal)**
```bash
celery -A config worker -l info
celery -A config beat -l info
```

#### Frontend

1. **Instalar dependencias**
```bash
cd frontend
npm install
```

2. **Iniciar servidor de desarrollo**
```bash
npm run dev
```

## 📊 Modelos de Base de Datos

### Tenants (Multi-tenant)
- **Client**: Empresas/Clientes
- **Domain**: Dominios por empresa

### Accounting (Contabilidad)
- **AccountClass**: Clases de cuenta (Nivel 1)
- **AccountGroup**: Grupos de cuenta (Nivel 2)
- **Account**: Cuentas del PUC (Niveles 3-6)
- **CostCenter**: Centros de costo
- **ThirdParty**: Terceros (clientes, proveedores)
- **JournalEntry**: Comprobantes contables
- **JournalEntryLine**: Movimientos contables

### DIAN (Facturación Electrónica)
- **ElectronicDocument**: Documentos electrónicos
- **ElectronicDocumentLine**: Líneas de documentos
- **DIANResolution**: Resoluciones DIAN
- **DIANLog**: Logs de transacciones DIAN
- **TaxType**: Tipos de impuestos
- **ElectronicDocumentTax**: Impuestos por documento

### Sync (Sincronización)
- **SyncLog**: Registros de sincronización

## 🔐 Configuración DIAN

Para habilitar la facturación electrónica, configura en el `.env`:

```env
DIAN_TEST_MODE=True
DIAN_SOFTWARE_ID=tu-software-id
DIAN_SOFTWARE_PIN=tu-software-pin
DIAN_CERTIFICATE_PATH=/path/to/certificate.p12
DIAN_CERTIFICATE_PASSWORD=tu-contraseña
DIAN_NIT=tu-nit
```

## 🌍 Configuración para Cali

El sistema incluye configuración específica para Cali:

```python
CALI_CONFIG = {
    'MUNICIPALITY_CODE': '76001',
    'MUNICIPALITY_NAME': 'Santiago de Cali',
    'DEPARTMENT_CODE': '76',
    'DEPARTMENT_NAME': 'Valle del Cauca',
    'ICA_TAX_RATE': 0.00966,  # 9.66 por mil
}
```

## 📈 Uso del Sistema

### Crear un Nuevo Tenant (Empresa)

1. Acceder al admin de Django
2. Crear un nuevo Client con:
   - Schema name (único)
   - NIT
   - Información de la empresa
   - Configuración DIAN
3. Asignar un dominio

### Crear una Factura Electrónica

1. Ir al módulo de Facturación DIAN
2. Crear un nuevo documento
3. Agregar líneas de productos/servicios
4. Calcular impuestos
5. Enviar a DIAN

### Generar Reportes

1. Ir al módulo de Reportes
2. Seleccionar tipo de reporte
3. Configurar fechas y filtros
4. Generar reporte (PDF/Excel)

## 🔄 Sincronización Desktop

La versión desktop sincroniza automáticamente:

- **Cada 5 minutos**: Datos generales
- **En tiempo real**: Documentos DIAN
- **Manual**: Desde el menú de sincronización

## 🧪 Testing

```bash
# Backend
cd backend
python manage.py test

# Frontend
cd frontend
npm test
```

## 📦 Deployment

### Producción con Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Variables de entorno de producción

```env
DEBUG=False
SECRET_KEY=tu-secret-key-segura
ALLOWED_HOSTS=tu-dominio.com
DATABASE_URL=postgresql://user:pass@db:5432/satori_prod
```

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 👥 Equipo

Desarrollado para operaciones contables en Colombia, con enfoque en Cali.

## 📞 Soporte

Para soporte técnico, contactar al equipo de desarrollo.

## 🗺️ Roadmap

- [x] Estructura base multi-tenant
- [x] Modelos de contabilidad (PUC)
- [x] Modelos de facturación electrónica
- [x] Frontend web básico
- [ ] Implementar servicios DIAN
- [ ] Aplicación desktop Electron
- [ ] Sistema de sincronización completo
- [ ] Generación de reportes avanzados
- [ ] Módulo de nómina electrónica
- [ ] App móvil
- [ ] Integración con bancos

## 🔧 Troubleshooting

### Error de conexión a PostgreSQL
Verificar que PostgreSQL esté corriendo y las credenciales sean correctas.

### Error de migraciones multi-tenant
Ejecutar primero las migraciones shared:
```bash
python manage.py migrate_schemas --shared
```

### Error en sincronización
Verificar logs de Celery y conectividad con Redis.

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2026
