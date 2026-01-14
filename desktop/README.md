# Sistema Desktop Satori (Electron)

Aplicación de escritorio del Sistema Contable Satori con funcionamiento offline y sincronización automática.

## ✨ Características

- **💾 Base de datos local SQLite** - Trabajo 100% offline
- **🔄 Sincronización automática** - Cuando hay conexión (cada 5 min)
- **📱 Interfaz idéntica a la web** - Usa el mismo código React
- **🔔 Notificaciones de escritorio** - Alertas de sincronización
- **🔐 Seguridad** - Context isolation y preload script
- **📊 Estadísticas de sync** - Monitor de sincronización

## 🏗️ Estructura

```
desktop/
├── main.js              # Proceso principal de Electron
├── preload.js           # Script de precarga (IPC seguro)
├── package.json         # Configuración y dependencias
├── src/
│   ├── database.js      # Gestor de SQLite
│   └── sync-service.js  # Servicio de sincronización
└── assets/
    └── icon.png         # Ícono de la aplicación
```

## 📦 Instalación

```bash
cd desktop
npm install
```

## 🚀 Desarrollo

```bash
# Iniciar aplicación en modo desarrollo
npm start

# La app se conectará al frontend en http://localhost:3001
```

## 🔧 Configuración

En el primer inicio, configurar:
- URL del servidor (ej: http://localhost:8000)
- Credenciales de usuario
- Empresa a sincronizar

## 📊 Base de Datos Local

La base de datos SQLite se crea automáticamente en:
- **Windows**: `%APPDATA%/satori-desktop/satori.db`
- **macOS**: `~/Library/Application Support/satori-desktop/satori.db`
- **Linux**: `~/.config/satori-desktop/satori.db`

### Esquema de tablas:
- `users` - Usuarios locales
- `accounts` - Plan de cuentas (PUC)
- `third_parties` - Clientes y proveedores
- `journal_entries` - Comprobantes contables
- `journal_entry_lines` - Movimientos
- `electronic_documents` - Facturas DIAN
- `sync_logs` - Historial de sincronización

## 🔄 Sincronización

### Automática
- Se ejecuta cada 5 minutos si hay conexión
- Solo sincroniza registros marcados con `needs_sync = 1`

### Manual
- Menú: Archivo → Sincronizar ahora
- Atajo: `Ctrl+R` (Windows/Linux) o `Cmd+R` (macOS)

### Proceso:
1. **PUSH**: Envía cambios locales al servidor
2. **PULL**: Recibe cambios del servidor
3. **Resolución**: Conflictos se resuelven por timestamp (last-write-wins)

## 🔌 API Expuesta

El preload script expone estas APIs al renderer:

```javascript
// Configuración
window.electronAPI.getConfig()
window.electronAPI.setConfig(config)

// Base de datos
window.electronAPI.dbQuery(sql, params)
window.electronAPI.dbTransaction(queries)

// Sincronización
window.electronAPI.syncNow()
window.electronAPI.checkConnection()
window.electronAPI.getSyncStats()

// Autenticación
window.electronAPI.authLogin(credentials)
window.electronAPI.authLogout()

// Eventos
window.electronAPI.onSyncStart(callback)
window.electronAPI.onSyncComplete(callback)
window.electronAPI.onConnectionChange(callback)
```

## 📦 Compilación

```bash
# Windows
npm run build:win

# macOS
npm run build:mac

# Linux
npm run build:linux
```

Los instaladores se generarán en `dist/`

## 🛠️ Tecnologías

- **Electron 28.1.3** - Framework de escritorio
- **better-sqlite3 9.2.2** - Base de datos SQLite
- **electron-store 8.1.0** - Almacenamiento de configuración
- **axios 1.6.5** - Cliente HTTP para sincronización
- **React 18.2.0** - Interfaz de usuario (compartida con web)

## 🔐 Seguridad

- ✅ `nodeIntegration: false` - Node.js no accesible en renderer
- ✅ `contextIsolation: true` - Aislamiento de contexto
- ✅ Preload script para IPC seguro
- ✅ Validación de datos en sincronización

## 📝 Notas

- La aplicación reutiliza los componentes React del frontend web
- En desarrollo se conecta a `http://localhost:3001` (Vite)
- En producción usa archivos estáticos empaquetados
- Los datos locales persisten entre cierres de la aplicación

## 🐛 Debug

Para abrir DevTools: `Ctrl+Shift+I` (Windows/Linux) o `Cmd+Option+I` (macOS)

## 📄 Licencia

PROPRIETARY - Satori Team
