# ===================================================================
# GUÍA DE MITIGACIÓN DE VULNERABILIDADES - SATORI
# ===================================================================

## 🔴 VULNERABILIDADES CORREGIDAS

### 1. IDOR Multi-Tenant (CRÍTICO) ✅ CORREGIDO
**Archivo:** `backend/apps/tenants/middleware.py`
**Cambio:** El middleware ahora valida que el `X-Client-Id` del header coincida con el `client_id` del JWT.
**Protección:** Un usuario no puede cambiar el header para acceder a datos de otra empresa.

### 2. Secretos Hardcoded (MEDIO/ALTO) ✅ CORREGIDO  
**Archivo:** `docker-compose.yml`
**Cambio:** Los secretos ahora se cargan desde variables de entorno:
- `GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}`
- `GOOGLE_SECRET=${GOOGLE_SECRET}`
- `ENCRYPTION_KEY=${ENCRYPTION_KEY}`
- `DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-default}`

### 3. ENCRYPTION_KEY Missing (ALTO) ✅ CORREGIDO
**Archivo:** `docker-compose.yml`
**Cambio:** Ahora se inyecta `ENCRYPTION_KEY` desde el archivo `.env` del servidor.

### 4. JWT Claims (SEGURIDAD) ✅ MEJORADO
**Archivo:** `backend/apps/core/serializers.py`
**Cambio:** El JWT ahora incluye siempre `client_id` en los claims para validación.

---

## 🛡️ PASOS PARA DEPLOYMENT SEGURO

### PASO 1: Generar Nuevas Credenciales Google OAuth
```bash
# 1. Ir a: https://console.cloud.google.com/apis/credentials
# 2. Crear nuevas credenciales OAuth 2.0
# 3. Configurar URIs autorizados:
#    - https://innovacode-mrb.com/accounts/google/login/callback/
# 4. COPIAR el nuevo Client ID y Secret
# 5. REVOCAR las credenciales antiguas INMEDIATAMENTE
```

### PASO 2: Crear Archivo .env en Servidor
```bash
# En tu máquina local:
scp .env.production.template root@178.156.215.106:/root/satori/.env

# Conectarse al servidor:
ssh root@178.156.215.106

# Editar el archivo:
nano /root/satori/.env

# Completar TODOS los valores <CAMBIAR>:
# - DJANGO_SECRET_KEY (generar nuevo)
# - ENCRYPTION_KEY (usar el existente de backend/.env.clean)
# - GOOGLE_CLIENT_ID (nuevas credenciales)
# - GOOGLE_SECRET (nuevas credenciales)

# Asegurar permisos:
chmod 600 /root/satori/.env
```

### PASO 3: Desplegar con Script Seguro
```bash
# En tu máquina local:
bash deploy_secure.sh
```

O manualmente:
```bash
# Empaquetar (sin .env)
tar --exclude='node_modules' --exclude='.venv' --exclude='__pycache__' \
    --exclude='.git' --exclude='db.sqlite3' --exclude='.env*' \
    -czf deploy.tar.gz backend frontend docker-compose.yml

# Enviar
scp deploy.tar.gz root@178.156.215.106:/root/satori/

# Desplegar en servidor
ssh root@178.156.215.106 "
    cd /root/satori
    tar -xzf deploy.tar.gz
    docker compose build
    docker compose down
    docker compose --env-file .env up -d
    docker image prune -f
"
```

---

## 🔍 VERIFICACIÓN POST-DEPLOYMENT

### Test 1: Verificar que las variables se cargaron
```bash
ssh root@178.156.215.106
docker compose exec backend env | grep -E 'GOOGLE|ENCRYPTION'
```
Debe mostrar las variables (sin valores completos por seguridad).

### Test 2: Probar Login con Google
```
https://innovacode-mrb.com/accounts/google/login/
```
Debe redirigir a Google OAuth sin error 500.

### Test 3: Verificar Protección IDOR
```bash
# En el frontend, interceptar una petición y cambiar el X-Client-Id
# El backend debe responder: 403 Forbidden
```

---

## ⚠️ VULNERABILIDAD PENDIENTE

### Git Leak (CRÍTICO) ⏳ PENDIENTE
**Estado:** Las credenciales antiguas están en el historial de Git.
**Acción Requerida:**
1. ✅ Rotar credenciales (nuevo Client ID/Secret)
2. ⏳ Limpiar historial Git o crear nuevo repositorio
3. ⏳ Forzar push con `--force` (PELIGROSO si hay colaboradores)

**Alternativa Segura:**
```bash
# Crear nuevo repositorio limpio
git checkout --orphan fresh-start
git add -A
git commit -m "feat: Sistema Satori - Inicio limpio sin credenciales"
git branch -D main
git branch -m main
git push -f origin main
```

---

## 📋 CHECKLIST DE SEGURIDAD

- [x] Validación JWT vs X-Client-Id implementada
- [x] Secretos movidos a variables de entorno
- [x] ENCRYPTION_KEY agregada al compose
- [x] Template .env.production creado
- [x] Script de deployment seguro creado
- [x] PyJWT agregado a requirements.txt
- [ ] Generar nuevas credenciales Google OAuth
- [ ] Desplegar con nuevo .env en servidor
- [ ] Revocar credenciales antiguas en Google Console
- [ ] Verificar login funcional
- [ ] Limpiar historial Git o crear repo nuevo

---

## 🆘 SOPORTE

Si encuentras errores durante el deployment:
1. Verificar logs: `docker compose logs backend`
2. Verificar .env: `cat /root/satori/.env` (en servidor)
3. Verificar permisos: `ls -la /root/satori/.env` (debe ser 600)
4. Reconstruir: `docker compose build --no-cache backend`

---

Fin del documento.
