# Changelog - Sistema Satori

Todos los cambios notables del proyecto serán documentados en este archivo.

## [1.0.0] - 2026-01-10

### 🎉 Versión Inicial - Base del Sistema Completada

#### Agregado

##### Backend Django
- ✅ Configuración completa de Django 5.0 con multi-tenant
- ✅ App `tenants`: Gestión de empresas multi-tenant
  - Modelo Client con información de empresas
  - Modelo Domain para dominios por tenant
  - Configuración DIAN por empresa
- ✅ App `accounting`: Sistema contable completo
  - Modelo AccountClass (Nivel 1 PUC)
  - Modelo AccountGroup (Nivel 2 PUC)
  - Modelo Account (Niveles 3-6 PUC)
  - Modelo CostCenter para centros de costo
  - Modelo ThirdParty para terceros (clientes, proveedores)
  - Modelo JournalEntry para comprobantes contables
  - Modelo JournalEntryLine para movimientos contables
- ✅ App `dian`: Facturación electrónica
  - Modelo ElectronicDocument para documentos electrónicos
  - Modelo ElectronicDocumentLine para líneas
  - Modelo DIANResolution para resoluciones
  - Modelo DIANLog para logs de transacciones
  - Modelo TaxType para tipos de impuestos
  - Modelo ElectronicDocumentTax para impuestos
- ✅ App `sync`: Sincronización
  - Modelo SyncLog para logs de sincronización
- ✅ Apps auxiliares: core, invoicing, taxes, reports
- ✅ API REST completa con Django REST Framework
- ✅ Autenticación JWT
- ✅ Configuración de Celery para tareas asíncronas
- ✅ Celery Beat para tareas programadas
- ✅ Admin panels para todos los modelos
- ✅ Serializers para API
- ✅ Views y ViewSets
- ✅ URLs configuradas

##### Frontend React
- ✅ Configuración con Vite + TypeScript
- ✅ Material-UI (MUI) v5
- ✅ React Router v6 para navegación
- ✅ MainLayout con sidebar navegable
- ✅ Dashboard con métricas
- ✅ Páginas para todos los módulos:
  - Dashboard
  - Plan de Cuentas
  - Comprobantes Contables
  - Terceros
  - Facturación Electrónica DIAN
  - Reportes
  - Configuración
  - Login
- ✅ Diseño responsive
- ✅ Tema profesional

##### Infraestructura
- ✅ Docker Compose completo
- ✅ Configuración PostgreSQL 15
- ✅ Configuración Redis 7
- ✅ Dockerfile para backend
- ✅ Configuración de servicios:
  - Backend Django
  - Celery Worker
  - Celery Beat
  - Frontend React
  - PostgreSQL
  - Redis

##### Documentación
- ✅ README.md principal completo
- ✅ QUICKSTART.md con guía de inicio
- ✅ TECHNICAL.md con documentación técnica
- ✅ ARCHITECTURE.md con diagramas
- ✅ COMMANDS.md con comandos útiles
- ✅ PROJECT_SUMMARY.md con resumen
- ✅ COMPLETION_REPORT.md con reporte
- ✅ STATUS.md con estado actual
- ✅ database_setup.sql para configuración

##### Configuración
- ✅ .env.example con variables de entorno
- ✅ .gitignore configurado
- ✅ requirements.txt con dependencias Python
- ✅ package.json para frontend
- ✅ Scripts de instalación (install.sh, install.bat)

##### Características Específicas Colombia
- ✅ Plan Único de Cuentas (PUC) colombiano
- ✅ Soporte para impuestos colombianos:
  - IVA (19%, 5%, 0%)
  - Retención en la Fuente
  - Retención de IVA
  - Retención de ICA
- ✅ Configuración específica para Cali:
  - Código de municipio: 76001
  - Tasa de ICA: 9.66 por mil
- ✅ Estructura para facturación electrónica DIAN:
  - CUFE/CUDE
  - XML UBL 2.1
  - Firma digital
  - Códigos QR

#### Pendiente

##### Desktop Electron
- ⚠️ Aplicación Electron completa
- ⚠️ Base de datos SQLite local
- ⚠️ Sincronización bidireccional
- ⚠️ Manejo de conflictos
- ⚠️ Instaladores

##### Implementación Funcional
- ⚠️ Servicios web DIAN (SOAP/REST)
- ⚠️ Generación de XML firmado
- ⚠️ Envío a DIAN
- ⚠️ Generación de PDF
- ⚠️ Reportes contables completos
- ⚠️ Validaciones de negocio avanzadas

##### Testing
- ⚠️ Tests unitarios
- ⚠️ Tests de integración
- ⚠️ Tests E2E
- ⚠️ Coverage

#### Cambios Técnicos

##### Dependencias
```
Backend:
- Django 5.0.1
- djangorestframework 3.14.0
- django-tenants 3.6.1
- psycopg2-binary 2.9.9
- celery 5.3.4
- redis 5.0.1
- djangorestframework-simplejwt 5.3.1
- Y más...

Frontend:
- React 18.2.0
- TypeScript 5.3.3
- @mui/material 5.15.4
- react-router-dom 6.21.3
- axios 1.6.5
- Y más...
```

##### Base de Datos
```
PostgreSQL 15 con:
- Schema compartido (public) para tenants
- Schemas individuales por tenant
- 16+ modelos principales
- ~100 campos en total
```

#### Notas de Implementación

##### Multi-Tenancy
- Cada empresa tiene su propio schema en PostgreSQL
- Datos completamente aislados
- Migraciones independientes por tenant
- Configuración individual por empresa

##### Configuración DIAN
Para usar facturación electrónica se requiere:
1. Certificado digital (.p12)
2. Software ID de DIAN
3. Resolución de facturación
4. Completar habilitación ante DIAN

##### Seguridad
- SECRET_KEY debe cambiarse en producción
- JWT para autenticación
- CORS configurado
- Passwords hasheados con Django
- HTTPS requerido en producción

#### Métricas del Proyecto

```
Archivos creados: ~65
Líneas de código: ~5,000
Modelos de BD: 16
Apps Django: 8
Páginas React: 7
Endpoints API: 30+
Documentos: 8
```

---

## [Próximas Versiones]

### [1.1.0] - Planificado
- Implementación completa de servicios DIAN
- Generación de reportes PDF/Excel
- Tests unitarios y de integración
- Fixtures con datos de ejemplo

### [1.2.0] - Planificado
- Aplicación Electron completa
- Sincronización bidireccional
- Manejo de conflictos
- Instaladores para Windows/Mac/Linux

### [2.0.0] - Futuro
- Módulo de nómina electrónica
- Integración con bancos
- App móvil
- BI y analytics

---

## Formato del Changelog

Este changelog sigue el formato de [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

### Tipos de Cambios
- **Agregado** para nuevas características.
- **Cambiado** para cambios en funcionalidad existente.
- **Obsoleto** para características que serán removidas.
- **Removido** para características removidas.
- **Corregido** para corrección de bugs.
- **Seguridad** para vulnerabilidades.

---

**Última actualización**: 2026-01-10
- Verificación y despliegue (14/01/2026): Se han desplegado los cambios para el inicio de sesión 'silencioso' (sin formulario intermedio). Se confirmó la configuración del adaptador personalizado.
- Verificación y despliegue (14/01/2026): Implementada lógica JIT para vincular automáticamente cuentas sociales a usuarios existentes por email, eliminando el bucle de 'Registrarse'.
