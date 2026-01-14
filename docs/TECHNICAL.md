# Documentación Técnica - Sistema Satori

## Plan Único de Cuentas (PUC) Colombiano

### Estructura del PUC

El Plan Único de Cuentas colombiano se estructura en 6 niveles:

#### Nivel 1: Clase (1 dígito)
- 1: Activo
- 2: Pasivo
- 3: Patrimonio
- 4: Ingresos
- 5: Gastos
- 6: Costos de Ventas
- 7: Costos de Producción o de Operación
- 8: Cuentas de Orden Deudoras
- 9: Cuentas de Orden Acreedoras

#### Nivel 2: Grupo (2 dígitos)
Ejemplo para Activos:
- 11: Disponible
- 12: Inversiones
- 13: Deudores
- 14: Inventarios
- 15: Propiedades, planta y equipo

#### Nivel 3: Cuenta (4 dígitos)
Ejemplo: 1105 - Caja

#### Nivel 4: Subcuenta (6 dígitos)
Ejemplo: 110505 - Caja General

#### Nivel 5 y 6: Auxiliares (8-10 dígitos)
Auxiliares específicos por empresa

## Facturación Electrónica DIAN

### Requisitos Técnicos

1. **Certificado Digital**
   - Formato P12
   - Emitido por entidad certificadora autorizada

2. **Software ID**
   - Obtenido de DIAN tras proceso de habilitación
   - Único por software

3. **Resolución de Facturación**
   - Autorización DIAN
   - Rango de numeración
   - Fecha de vigencia

### Proceso de Facturación

1. **Creación del Documento**
   ```python
   document = ElectronicDocument.objects.create(
       document_type='INVOICE',
       customer=customer,
       issue_date=date.today(),
       # ...
   )
   ```

2. **Generación de CUFE**
   ```
   CUFE = SHA-384(
       NumFac + FecFac + HorFac + ValFac + CodImp1 + 
       ValImp1 + CodImp2 + ValImp2 + CodImp3 + ValImp3 + 
       ValTot + NitOFE + NumAdq + Software-PIN + TipoAmbie
   )
   ```

3. **Firma Digital**
   - Usar certificado P12
   - Firmar XML con XMLDSig

4. **Envío a DIAN**
   - Endpoint: `https://vpfe.dian.gov.co/WcfDianCustomerServices.svc`
   - Método: SOAP SendBillSync

5. **Validación**
   - DIAN responde con estado
   - Guardar respuesta en DIANLog

### Estructura XML UBL 2.1

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2">
  <cbc:UBLVersionID>UBL 2.1</cbc:UBLVersionID>
  <cbc:CustomizationID>...</cbc:CustomizationID>
  <cbc:ProfileID>DIAN 2.1</cbc:ProfileID>
  <cbc:ID>SETP990000001</cbc:ID>
  <cbc:UUID>...</cbc:UUID>
  <cbc:IssueDate>2024-01-01</cbc:IssueDate>
  <cbc:IssueTime>10:00:00-05:00</cbc:IssueTime>
  <!-- ... más elementos ... -->
</Invoice>
```

## Impuestos Colombianos

### IVA (Impuesto al Valor Agregado)

**Tarifas:**
- General: 19%
- Reducida: 5%
- Excluidos: 0%

**Cuentas PUC:**
- 2408: IVA por pagar
- 2365: Retención de IVA

### Retención en la Fuente

**Conceptos principales:**
- Servicios: 4%
- Honorarios: 11%
- Compras: 2.5%
- Arrendamientos: 3.5%

**Cuentas PUC:**
- 2365: Retenciones por pagar
- 1355: Retenciones a favor

### Retención de ICA (Cali)

**Tasa para Cali:** 9.66 por mil (0.966%)

**Cuentas:**
- 2368: ReteICA por pagar

## API Endpoints

### Autenticación
```
POST /api/auth/token/
POST /api/auth/token/refresh/
```

### Tenants
```
GET    /api/tenants/clients/
POST   /api/tenants/clients/
GET    /api/tenants/clients/{id}/
PUT    /api/tenants/clients/{id}/
DELETE /api/tenants/clients/{id}/
POST   /api/tenants/clients/{id}/sync/
```

### Accounting
```
GET    /api/accounting/accounts/
POST   /api/accounting/accounts/
GET    /api/accounting/journal-entries/
POST   /api/accounting/journal-entries/
GET    /api/accounting/third-parties/
GET    /api/accounting/balance-sheet/
GET    /api/accounting/trial-balance/
GET    /api/accounting/income-statement/
```

### DIAN
```
GET    /api/dian/documents/
POST   /api/dian/documents/
POST   /api/dian/send/{id}/
POST   /api/dian/validate/{id}/
GET    /api/dian/generate-pdf/{id}/
GET    /api/dian/resolutions/
```

## Sincronización Desktop-Web

### Arquitectura

```
Desktop (SQLite) <---> API REST <---> PostgreSQL (Server)
```

### Proceso de Sincronización

1. **Push (Desktop → Server)**
   ```python
   # Desktop envía cambios
   changes = get_local_changes()
   response = api.post('/api/sync/push/', data=changes)
   mark_as_synced(changes)
   ```

2. **Pull (Server → Desktop)**
   ```python
   # Desktop recibe cambios
   last_sync = get_last_sync_timestamp()
   changes = api.get(f'/api/sync/pull/?since={last_sync}')
   apply_changes(changes)
   ```

3. **Resolución de Conflictos**
   - Last-write-wins
   - Timestamp de modificación
   - Logs de conflictos

### Tablas de Sincronización

```python
class SyncLog(models.Model):
    client_id = CharField()
    sync_type = CharField()
    status = CharField()
    records_sent = IntegerField()
    records_received = IntegerField()
    started_at = DateTimeField()
    completed_at = DateTimeField()
```

## Seguridad

### Autenticación
- JWT tokens
- Refresh tokens
- Expiración configurable

### Autorización
- Permisos por tenant
- Roles de usuario
- Permisos por módulo

### Encriptación
- HTTPS en producción
- Certificados SSL
- Encriptación de datos sensibles

### Multi-tenant Security
- Aislamiento total de datos
- Schema por tenant
- Validación de acceso

## Performance

### Optimizaciones

1. **Database**
   - Índices en campos frecuentes
   - Particionamiento por tenant
   - Query optimization

2. **Caching**
   - Redis para sesiones
   - Cache de consultas frecuentes
   - Cache de reportes

3. **Background Tasks**
   - Celery para tareas pesadas
   - Sincronización asíncrona
   - Generación de reportes

## Monitoreo

### Logs

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/satori.log',
        },
    },
    'loggers': {
        'apps': {
            'level': 'DEBUG',
        },
    },
}
```

### Métricas
- Celery Beat para tareas programadas
- Monitoreo de sincronizaciones
- Logs de errores DIAN

## Backup y Recuperación

### Backup Automático
```bash
# PostgreSQL
pg_dump satori_db > backup_$(date +%Y%m%d).sql

# Archivos
tar -czf media_backup.tar.gz media/
```

### Restore
```bash
psql satori_db < backup_20240101.sql
```

## Mantenimiento

### Tareas Periódicas

1. **Diarias**
   - Backup de base de datos
   - Limpieza de logs antiguos
   - Verificación de sincronizaciones

2. **Semanales**
   - Optimización de base de datos
   - Revisión de espacio en disco
   - Actualización de certificados

3. **Mensuales**
   - Auditoría de seguridad
   - Revisión de performance
   - Actualización de dependencias
