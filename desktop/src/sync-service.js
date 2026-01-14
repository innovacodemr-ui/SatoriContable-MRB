/**
 * Servicio de sincronización Desktop <-> Servidor
 */

const axios = require('axios');
const { BrowserWindow } = require('electron');

class SyncService {
  constructor(database, store) {
    this.database = database;
    this.store = store;
    this.serverUrl = store.get('serverUrl', 'http://localhost:8000');
    this.online = false;
    this.syncing = false;
    this.syncInterval = null;
  }

  /**
   * Actualizar URL del servidor
   */
  updateServerUrl(url) {
    this.serverUrl = url;
    this.store.set('serverUrl', url);
  }

  /**
   * Verificar conectividad con el servidor
   */
  async checkConnection() {
    try {
      const response = await axios.get(`${this.serverUrl}/api/health/`, {
        timeout: 5000
      });
      
      const wasOffline = !this.online;
      this.online = response.status === 200;
      
      // Notificar cambio de estado
      if (wasOffline && this.online) {
        this.notifyConnectionChange(true);
        console.log('✓ Conexión establecida con el servidor');
      }
      
      return this.online;
    } catch (error) {
      const wasOnline = this.online;
      this.online = false;
      
      if (wasOnline) {
        this.notifyConnectionChange(false);
        console.log('✗ Sin conexión con el servidor');
      }
      
      return false;
    }
  }

  /**
   * Verificar si está en línea
   */
  isOnline() {
    return this.online;
  }

  /**
   * Realizar sincronización completa
   */
  async performSync(manual = false) {
    // Si ya está sincronizando, no hacer nada
    if (this.syncing) {
      console.log('⚠ Sincronización ya en progreso');
      return { success: false, message: 'Sincronización en progreso' };
    }

    // Verificar conexión
    const isConnected = await this.checkConnection();
    if (!isConnected) {
      return { success: false, message: 'Sin conexión al servidor' };
    }

    this.syncing = true;
    this.notifySyncStart();

    const startTime = Date.now();
    const syncLog = {
      sync_type: 'FULL',
      status: 'IN_PROGRESS',
      records_sent: 0,
      records_received: 0,
      records_failed: 0
    };

    try {
      // Registrar inicio de sincronización
      const logId = this.database.run(
        `INSERT INTO sync_logs (sync_type, status, started_at) 
         VALUES (?, 'IN_PROGRESS', datetime('now'))`,
        ['FULL']
      ).lastInsertRowid;

      // PASO 1: Enviar cambios locales al servidor (PUSH)
      console.log('→ Enviando cambios locales...');
      const pushResult = await this.pushLocalChanges();
      syncLog.records_sent = pushResult.sent;
      syncLog.records_failed += pushResult.failed;

      // PASO 2: Obtener cambios del servidor (PULL)
      console.log('← Recibiendo cambios del servidor...');
      const pullResult = await this.pullServerChanges();
      syncLog.records_received = pullResult.received;
      syncLog.records_failed += pullResult.failed;

      // Actualizar log de sincronización
      this.database.run(
        `UPDATE sync_logs SET status = 'COMPLETED', 
         records_sent = ?, records_received = ?, records_failed = ?,
         completed_at = datetime('now')
         WHERE id = ?`,
        [syncLog.records_sent, syncLog.records_received, syncLog.records_failed, logId]
      );

      // Guardar timestamp de última sincronización
      this.store.set('lastSync', new Date().toISOString());

      const duration = Date.now() - startTime;
      console.log(`✓ Sincronización completada en ${duration}ms`);

      this.notifySyncComplete({
        sent: syncLog.records_sent,
        received: syncLog.records_received,
        failed: syncLog.records_failed,
        duration
      });

      return {
        success: true,
        sent: syncLog.records_sent,
        received: syncLog.records_received,
        failed: syncLog.records_failed,
        duration
      };

    } catch (error) {
      console.error('Error en sincronización:', error);
      
      this.database.run(
        `UPDATE sync_logs SET status = 'FAILED', 
         error_message = ?, completed_at = datetime('now')
         WHERE id = ?`,
        [error.message, logId]
      );

      this.notifySyncError(error.message);

      return {
        success: false,
        error: error.message
      };
    } finally {
      this.syncing = false;
    }
  }

  /**
   * Enviar cambios locales al servidor
   */
  async pushLocalChanges() {
    const token = this.store.get('token');
    const pending = this.database.getPendingSync();
    
    let sent = 0;
    let failed = 0;

    // Si no hay cambios pendientes
    if (Object.keys(pending).length === 0) {
      console.log('  No hay cambios locales para enviar');
      return { sent, failed };
    }

    try {
      // Enviar datos al endpoint de sincronización
      const response = await axios.post(
        `${this.serverUrl}/api/sync/push/`,
        { changes: pending },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          timeout: 30000
        }
      );

      if (response.data.success) {
        // Marcar registros como sincronizados
        for (const [table, records] of Object.entries(pending)) {
          const ids = records.map(r => r.id);
          this.database.markAsSynced(table, ids);
          sent += records.length;
        }
        
        console.log(`  ✓ ${sent} registros enviados`);
      }

    } catch (error) {
      console.error('  Error al enviar cambios:', error.message);
      failed = Object.values(pending).reduce((sum, records) => sum + records.length, 0);
    }

    return { sent, failed };
  }

  /**
   * Obtener cambios del servidor
   */
  async pullServerChanges() {
    const token = this.store.get('token');
    const lastSync = this.store.get('lastSync');
    
    let received = 0;
    let failed = 0;

    try {
      // Obtener cambios desde la última sincronización
      const response = await axios.get(
        `${this.serverUrl}/api/sync/pull/`,
        {
          params: { since: lastSync },
          headers: {
            'Authorization': `Bearer ${token}`
          },
          timeout: 30000
        }
      );

      if (response.data.success) {
        const changes = response.data.changes;

        // Aplicar cambios en orden
        const tables = [
          'accounts', 'third_parties', 'cost_centers',
          'dian_formats', 'dian_concepts',
          'journal_entries', 'journal_entry_lines',
          'electronic_documents', 'electronic_document_lines',
          'electronic_document_taxes'
        ];

        for (const table of tables) {
          if (changes[table] && changes[table].length > 0) {
            try {
              await this.applyServerChanges(table, changes[table]);
              received += changes[table].length;
            } catch (error) {
              console.error(`  Error al aplicar cambios en ${table}:`, error.message);
              failed += changes[table].length;
            }
          }
        }

        console.log(`  ✓ ${received} registros recibidos`);
      }

    } catch (error) {
      console.error('  Error al recibir cambios:', error.message);
    }

    return { received, failed };
  }

  /**
   * Aplicar cambios del servidor en la base de datos local
   */
  async applyServerChanges(table, records) {
    for (const record of records) {
      try {
        // Resolver Claves Foráneas (FK) basados en server_id
        if (table === 'dian_concepts' && record.dian_format_id) {
            const format = this.database.query('SELECT id FROM dian_formats WHERE server_id = ?', [record.dian_format_id]);
            if (format.length > 0) record.dian_format_id = format[0].id;
        }

        // Verificar si el registro ya existe (por server_id)
        const existing = this.database.query(
          `SELECT id FROM ${table} WHERE server_id = ?`,
          [record.id]
        );

        if (existing.length > 0) {
          // Actualizar registro existente
          const fields = Object.keys(record).filter(k => k !== 'id');
          const setClause = fields.map(f => `${f} = ?`).join(', ');
          const values = fields.map(f => record[f]);
          values.push(record.id);

          this.database.run(
            `UPDATE ${table} SET ${setClause}, needs_sync = 0 WHERE server_id = ?`,
            values
          );
        } else {
          // Insertar nuevo registro
          const fields = Object.keys(record);
          const placeholders = fields.map(() => '?').join(', ');
          const values = fields.map(f => record[f]);

          this.database.run(
            `INSERT INTO ${table} (${fields.join(', ')}, server_id, needs_sync) 
             VALUES (${placeholders}, ?, 0)`,
            [...values, record.id]
          );
        }
      } catch (error) {
        console.error(`  Error al aplicar registro en ${table}:`, error);
        throw error;
      }
    }
  }

  /**
   * Obtener estadísticas de sincronización
   */
  async getSyncStats() {
    const lastSync = this.store.get('lastSync');
    const stats = this.database.getStats();
    
    const recentLogs = this.database.query(
      `SELECT * FROM sync_logs ORDER BY started_at DESC LIMIT 10`
    );

    return {
      lastSync,
      online: this.online,
      pendingSync: stats.pendingSync,
      totalRecords: stats.accounts + stats.thirdParties + 
                    stats.journalEntries + stats.electronicDocuments,
      recentSyncs: recentLogs
    };
  }

  /**
   * Detener servicio
   */
  stop() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
  }

  // ===== Métodos de notificación =====

  notifySyncStart() {
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(win => {
      win.webContents.send('sync-start');
    });
  }

  notifySyncComplete(data) {
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(win => {
      win.webContents.send('sync-complete', data);
    });
  }

  notifySyncError(error) {
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(win => {
      win.webContents.send('sync-error', error);
    });
  }

  notifyConnectionChange(online) {
    const windows = BrowserWindow.getAllWindows();
    windows.forEach(win => {
      win.webContents.send('connection-change', { online });
    });
  }
}

module.exports = SyncService;
