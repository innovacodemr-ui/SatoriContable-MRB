# Satori Desktop - Guía de Inicio Rápido

## 📋 Pre-requisitos

1. **Node.js 18+** instalado
2. **Frontend web corriendo** en http://localhost:3001
3. **Backend Django** corriendo en http://localhost:8000 (opcional para sincronización)

## 🚀 Iniciar la Aplicación

### Opción 1: Modo Desarrollo (Recomendado)

```bash
# Instalar dependencias (solo la primera vez)
cd desktop
npm install

# Iniciar aplicación
npm start
```

La aplicación se abrirá y cargará la interfaz desde http://localhost:3001

### Opción 2: Compilar y Ejecutar

```bash
# Compilar para tu sistema operativo
npm run pack

# El ejecutable estará en dist/
```

## ⚙️ Configuración Inicial

Al iniciar por primera vez:

1. **Configurar servidor**: Ir a Configuración → URL del Servidor
   - Por defecto: `http://localhost:8000`
   
2. **Iniciar sesión**: Usar credenciales de usuario
   - Los datos se guardan en SQLite local

3. **Sincronización**: Se activa automáticamente cada 5 minutos

## 🔄 Funcionalidades Principales

### Trabajo Offline
- Todos los datos se guardan en SQLite local
- No requiere conexión para trabajar
- Los cambios se marcan para sincronización posterior

### Sincronización
- **Automática**: Cada 5 minutos (si hay conexión)
- **Manual**: Menú → Archivo → Sincronizar ahora (Ctrl+R)
- **Bidireccional**: Push (local → servidor) y Pull (servidor → local)

### Base de Datos Local
Ubicación según sistema operativo:
- Windows: `%APPDATA%\satori-desktop\satori.db`
- macOS: `~/Library/Application Support/satori-desktop/satori.db`
- Linux: `~/.config/satori-desktop/satori.db`

## 🐛 Solución de Problemas

### La aplicación no inicia
```bash
# Verificar versión de Node.js
node --version  # Debe ser 18 o superior

# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

### Error de conexión con el frontend
- Asegúrate de que el frontend web esté corriendo en puerto 3001
- Verifica con: http://localhost:3001

### Error de sincronización
- Verifica que el backend esté corriendo en puerto 8000
- Verifica conexión a Internet
- Revisa logs en la aplicación: Ver → Herramientas de desarrollo

### No aparecen datos
- Primera vez: Necesitas hacer login
- Sin datos locales: Hacer sincronización manual
- Verifica que la base de datos SQLite se haya creado correctamente

## 🎯 Atajos de Teclado

- `Ctrl+R` / `Cmd+R` - Sincronizar ahora
- `Ctrl+Shift+I` / `Cmd+Option+I` - Abrir DevTools
- `Ctrl+Q` / `Cmd+Q` - Salir
- `F11` - Pantalla completa

## 📊 Verificar Estado

### Estadísticas de Sincronización
```javascript
// En DevTools Console
const stats = await window.electronAPI.getSyncStats()
console.log(stats)
```

### Verificar Conexión
```javascript
// En DevTools Console
const status = await window.electronAPI.checkConnection()
console.log(status)
```

### Consultar Base de Datos
```javascript
// En DevTools Console
const accounts = await window.db.getAccounts()
console.log(accounts)
```

## 📦 Compilar para Distribución

### Windows
```bash
npm run build:win
# Genera instalador en dist/Satori-Setup-1.0.0.exe
```

### macOS
```bash
npm run build:mac
# Genera .dmg en dist/Satori-1.0.0.dmg
```

### Linux
```bash
npm run build:linux
# Genera .AppImage en dist/Satori-1.0.0.AppImage
```

## 🔧 Desarrollo

### Estructura de Archivos
- `main.js` - Proceso principal (backend de Electron)
- `preload.js` - Bridge seguro entre main y renderer
- `src/database.js` - Gestor de SQLite
- `src/sync-service.js` - Lógica de sincronización

### Debugging
1. Abrir DevTools: `Ctrl+Shift+I`
2. Ver logs del main process en la terminal
3. Ver logs del renderer en DevTools Console

### Modificar Código
- Cambios en `main.js`, `preload.js` o `src/`: Reiniciar app
- Cambios en frontend React: Auto-reload (Vite HMR)

## 🎨 Personalización

### Cambiar ícono
Reemplaza `assets/icon.png` con tu ícono (512x512 px)

### Cambiar nombre
Edita `package.json`:
```json
{
  "name": "tu-nombre-app",
  "productName": "Tu App",
  "description": "Tu descripción"
}
```

## 📚 Más Información

- [Documentación Electron](https://www.electronjs.org/docs)
- [API de better-sqlite3](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md)
- [Electron Builder](https://www.electron.build/)

## 🆘 Soporte

Para reportar bugs o solicitar ayuda, contactar al equipo de desarrollo.
