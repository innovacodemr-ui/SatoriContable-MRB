const { app, BrowserWindow, ipcMain, Menu, dialog } = require('electron');
const path = require('path');
const Store = require('electron-store');
const Database = require('./src/database');
const SyncService = require('./src/sync-service');
const PUCLoader = require('./src/load-puc');
const TestDataLoader = require('./src/load-test-data');

// Inicializar almacenamiento persistente
const store = new Store();

// Variables globales
let mainWindow;
let database;
let syncService;
let pucLoader;
let testDataLoader;

// Configuración de la aplicación
const isDevelopment = process.env.NODE_ENV !== 'production';
// IP de Producción Hetzner como default
const DEFAULT_SERVER_URL = 'http://178.156.215.106:8000';
const serverUrl = store.get('serverUrl', isDevelopment ? 'http://localhost:8000' : DEFAULT_SERVER_URL);

/**
 * Crear ventana principal
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      // Seguridad adicional
      sandbox: true,
      webSecurity: true
    },
    show: false // No mostrar hasta que esté listo
  });

  // Configurar Content-Security-Policy
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': isDevelopment 
          ? ["default-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:* ws://localhost:*"]
          : ["default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"]
      }
    });
  });

  // Cargar la aplicación
  
  // ESTRATEGIA DE ACTUALIZACIÓN AUTOMÁTICA (SaaS):
  // En lugar de cargar archivos locales (que requerirían reinstalar el .exe para ver cambios),
  // cargamos la URL remota de Hertzner. Así, cualquier despliegue en la nube actualiza a todos.
  const REMOTE_URL = 'http://178.156.215.106'; 
  
  if (isDevelopment) {
    // En desarrollo, cargar desde el servidor de Vite local
    mainWindow.loadURL('http://localhost:3000');
    mainWindow.webContents.openDevTools();
  } else {
    // En producción, cargar desde LA NUBE (Frontend servido por Nginx en Hetzner)
    // Esto convierte la app en un "Wrapper" o "Navegador Dedicado"
    console.log(`Cargando Satori Cloud desde: ${REMOTE_URL}`);
    mainWindow.loadURL(REMOTE_URL);
    
    // Fallback opcional: Si no hay internet, podría intentar cargar localFile
    // pero por ahora forzamos la nube para garantizar consistencia.
  }

  // Mostrar ventana cuando esté lista
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Verificar conexión e iniciar sincronización
    if (syncService) {
      syncService.checkConnection();
    }
  });

  // Cerrar la aplicación cuando se cierra la ventana
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * Crear menú de la aplicación
 */
function createMenu() {
  const template = [
    {
      label: 'Archivo',
      submenu: [
        {
          label: 'Configuración',
          click: () => {
            mainWindow.webContents.send('navigate', '/settings');
          }
        },
        { type: 'separator' },
        {
          label: 'Sincronizar ahora',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            if (syncService) {
              syncService.performSync(true);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Salir',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Editar',
      submenu: [
        { role: 'undo', label: 'Deshacer' },
        { role: 'redo', label: 'Rehacer' },
        { type: 'separator' },
        { role: 'cut', label: 'Cortar' },
        { role: 'copy', label: 'Copiar' },
        { role: 'paste', label: 'Pegar' },
        { role: 'selectAll', label: 'Seleccionar todo' }
      ]
    },
    {
      label: 'Ver',
      submenu: [
        { role: 'reload', label: 'Recargar' },
        { role: 'toggleDevTools', label: 'Herramientas de desarrollo' },
        { type: 'separator' },
        { role: 'resetZoom', label: 'Zoom normal' },
        { role: 'zoomIn', label: 'Acercar' },
        { role: 'zoomOut', label: 'Alejar' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Pantalla completa' }
      ]
    },
    {
      label: 'Ayuda',
      submenu: [
        {
          label: 'Acerca de Satori',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'Acerca de Satori',
              message: 'Sistema Contable Satori',
              detail: `Versión: ${app.getVersion()}\nSistema de contabilidad multi-empresa para Colombia\ncon integración DIAN`,
              buttons: ['OK']
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Documentación',
          click: () => {
            require('electron').shell.openExternal('https://docs.satori.com');
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

/**
 * Inicializar base de datos y servicios
 */
async function initializeServices() {
  try {
    // Inicializar base de datos SQLite
    database = new Database();
    await database.initialize();

    // Inicializar cargador de PUC
    pucLoader = new PUCLoader(database);

    // Inicializar cargador de datos de prueba
    testDataLoader = new TestDataLoader(database);

    // Inicializar servicio de sincronización
    syncService = new SyncService(database, store);
    
    // Configurar sincronización automática cada 5 minutos
    setInterval(() => {
      if (syncService.isOnline()) {
        syncService.performSync(false);
      }
    }, 5 * 60 * 1000);

    console.log('✓ Servicios inicializados correctamente');
  } catch (error) {
    console.error('Error al inicializar servicios:', error);
    dialog.showErrorBox(
      'Error de inicialización',
      'No se pudieron inicializar los servicios de la aplicación.'
    );
  }
}

// ==================== IPC HANDLERS ====================

/**
 * Obtener configuración
 */
ipcMain.handle('get-config', async () => {
  return {
    serverUrl: store.get('serverUrl', 'http://localhost:8000'),
    companyId: store.get('companyId'),
    userId: store.get('userId'),
    token: store.get('token'),
    lastSync: store.get('lastSync'),
    autoSync: store.get('autoSync', true)
  };
});

/**
 * Guardar configuración
 */
ipcMain.handle('set-config', async (event, config) => {
  Object.keys(config).forEach(key => {
    store.set(key, config[key]);
  });
  
  // Actualizar URL del servidor en el servicio de sincronización
  if (config.serverUrl && syncService) {
    syncService.updateServerUrl(config.serverUrl);
  }
  
  return { success: true };
});

/**
 * Ejecutar consulta SQL
 */
ipcMain.handle('db-query', async (event, sql, params = []) => {
  try {
    const result = await database.query(sql, params);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error en consulta DB:', error);
    return { success: false, error: error.message };
  }
});

/**
 * Ejecutar múltiples consultas en transacción
 */
ipcMain.handle('db-transaction', async (event, queries) => {
  try {
    const result = await database.transaction(queries);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error en transacción DB:', error);
    return { success: false, error: error.message };
  }
});

/**
 * Sincronizar datos
 */
ipcMain.handle('sync-now', async () => {
  try {
    const result = await syncService.performSync(true);
    return { success: true, data: result };
  } catch (error) {
    console.error('Error en sincronización:', error);
    return { success: false, error: error.message };
  }
});

/**
 * Verificar estado de conexión
 */
ipcMain.handle('check-connection', async () => {
  try {
    const isOnline = await syncService.checkConnection();
    return { success: true, online: isOnline };
  } catch (error) {
    return { success: false, online: false };
  }
});

/**
 * Obtener estadísticas de sincronización
 */
ipcMain.handle('get-sync-stats', async () => {
  try {
    const stats = await syncService.getSyncStats();
    return { success: true, data: stats };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

/**
 * Login local (verificar credenciales en SQLite)
 */
ipcMain.handle('auth-login', async (event, credentials) => {
  try {
    const { username, password } = credentials;
    
    // Verificar en base de datos local
    const user = await database.query(
      'SELECT * FROM users WHERE username = ? AND is_active = 1',
      [username]
    );
    
    if (user.length === 0) {
      return { success: false, error: 'Usuario no encontrado' };
    }
    
    // TODO: Verificar password hasheado
    // Por ahora comparación simple
    if (user[0].password !== password) {
      return { success: false, error: 'Contraseña incorrecta' };
    }
    
    // Guardar sesión
    store.set('userId', user[0].id);
    store.set('username', user[0].username);
    store.set('isAuthenticated', true);
    
    return {
      success: true,
      user: {
        id: user[0].id,
        username: user[0].username,
        email: user[0].email,
        fullName: user[0].full_name
      }
    };
  } catch (error) {
    console.error('Error en login:', error);
    return { success: false, error: error.message };
  }
});

/**
 * Logout
 */
ipcMain.handle('auth-logout', async () => {
  store.delete('userId');
  store.delete('username');
  store.delete('token');
  store.set('isAuthenticated', false);
  return { success: true };
});

/**
 * Cargar PUC (Plan Único de Cuentas)
 */
ipcMain.handle('load-puc', async () => {
  try {
    if (!pucLoader) {
      pucLoader = new PUCLoader();
    }
    const result = await pucLoader.loadPUC();
    return { success: true, ...result };
  } catch (error) {
    console.error('Error al cargar PUC:', error);
    return { success: false, error: error.message };
  }
});

/**
 * Cargar datos de prueba
 */
ipcMain.handle('load-test-data', async () => {
  try {
    if (!testDataLoader) {
      testDataLoader = new TestDataLoader();
    }
    const result = await testDataLoader.loadTestData();
    return { success: true, ...result };
  } catch (error) {
    console.error('Error al cargar datos de prueba:', error);
    return { success: false, error: error.message };
  }
});

// ==================== EVENTOS DE LA APLICACIÓN ====================

/**
 * Cuando Electron termina de inicializar
 */
app.whenReady().then(async () => {
  await initializeServices();
  createWindow();
  createMenu();

  // En macOS, recrear ventana cuando se hace clic en el dock
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

/**
 * Cerrar cuando todas las ventanas están cerradas (excepto en macOS)
 */
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * Antes de cerrar la aplicación
 */
app.on('before-quit', async (event) => {
  event.preventDefault();
  
  try {
    // Cerrar base de datos
    if (database) {
      await database.close();
    }
    
    // Detener sincronización
    if (syncService) {
      syncService.stop();
    }
    
    app.exit(0);
  } catch (error) {
    console.error('Error al cerrar aplicación:', error);
    app.exit(1);
  }
});

// Manejar errores no capturados
process.on('uncaughtException', (error) => {
  console.error('Error no capturado:', error);
  dialog.showErrorBox('Error', error.message);
});
