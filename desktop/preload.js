/**
 * Preload script para Electron
 * Expone APIs seguras al renderer process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Exponer API al contexto del renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Configuración
  getConfig: () => ipcRenderer.invoke('get-config'),
  setConfig: (config) => ipcRenderer.invoke('set-config', config),

  // Base de datos
  dbQuery: (sql, params) => ipcRenderer.invoke('db-query', sql, params),
  dbTransaction: (queries) => ipcRenderer.invoke('db-transaction', queries),

  // Sincronización
  syncNow: () => ipcRenderer.invoke('sync-now'),
  checkConnection: () => ipcRenderer.invoke('check-connection'),
  getSyncStats: () => ipcRenderer.invoke('get-sync-stats'),

  // Autenticación
  authLogin: (credentials) => ipcRenderer.invoke('auth-login', credentials),
  authLogout: () => ipcRenderer.invoke('auth-logout'),

  // Eventos
  onSyncStart: (callback) => ipcRenderer.on('sync-start', callback),
  onSyncComplete: (callback) => ipcRenderer.on('sync-complete', callback),
  onSyncError: (callback) => ipcRenderer.on('sync-error', callback),
  onConnectionChange: (callback) => ipcRenderer.on('connection-change', callback),
  onNavigate: (callback) => ipcRenderer.on('navigate', callback),

  // Cargar datos iniciales
  loadPUC: () => ipcRenderer.invoke('load-puc'),
  loadTestData: () => ipcRenderer.invoke('load-test-data'),

  // Información del sistema
  platform: process.platform,
  version: process.versions.electron,
  isDesktop: true
});

// Exponer API de base de datos local
contextBridge.exposeInMainWorld('db', {
  // Accounts (Cuentas)
  getAccounts: async (filters = {}) => {
    const { search, accountType, level } = filters;
    let sql = 'SELECT * FROM accounts WHERE 1=1';
    const params = [];

    if (search) {
      sql += ' AND (code LIKE ? OR name LIKE ?)';
      params.push(`%${search}%`, `%${search}%`);
    }
    if (accountType) {
      sql += ' AND account_type = ?';
      params.push(accountType);
    }
    if (level) {
      sql += ' AND level = ?';
      params.push(level);
    }

    sql += ' ORDER BY code';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createAccount: async (account) => {
    const sql = `
      INSERT INTO accounts (code, name, level, nature, account_type, 
        allows_movement, requires_third_party, requires_cost_center, 
        is_tax_account, tax_type, parent_id, created_at, needs_sync)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
    `;
    return ipcRenderer.invoke('db-query', sql, [
      account.code, account.name, account.level, account.nature,
      account.accountType, account.allowsMovement ? 1 : 0,
      account.requiresThirdParty ? 1 : 0, account.requiresCostCenter ? 1 : 0,
      account.isTaxAccount ? 1 : 0, account.taxType, account.parentId
    ]);
  },

  updateAccount: async (id, account) => {
    const sql = `
      UPDATE accounts SET name = ?, allows_movement = ?, 
        requires_third_party = ?, requires_cost_center = ?,
        is_tax_account = ?, tax_type = ?, 
        dian_format_id = ?, dian_concept_id = ?,
        updated_at = datetime('now'), needs_sync = 1
      WHERE id = ?
    `;
    return ipcRenderer.invoke('db-query', sql, [
      account.name, account.allowsMovement ? 1 : 0,
      account.requiresThirdParty ? 1 : 0, account.requiresCostCenter ? 1 : 0,
      account.isTaxAccount ? 1 : 0, account.taxType, 
      account.dian_format, account.dian_concept, // IDs FK
      id
    ]);
  },

  // DIAN Formats & Concepts
  getDianFormats: async () => {
    return ipcRenderer.invoke('db-query', 'SELECT * FROM dian_formats ORDER BY code', []);
  },

  getDianConcepts: async (formatId) => {
    let sql = 'SELECT * FROM dian_concepts WHERE 1=1';
    const params = [];
    
    if (formatId) {
      sql += ' AND dian_format_id = ?';
      params.push(formatId);
    }
    
    sql += ' ORDER BY code';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  // Journal Entries (Comprobantes)
  getJournalEntries: async (filters = {}) => {
    const { startDate, endDate, entryType, status } = filters;
    let sql = 'SELECT * FROM journal_entries WHERE 1=1';
    const params = [];

    if (startDate) {
      sql += ' AND date >= ?';
      params.push(startDate);
    }
    if (endDate) {
      sql += ' AND date <= ?';
      params.push(endDate);
    }
    if (entryType) {
      sql += ' AND entry_type = ?';
      params.push(entryType);
    }
    if (status) {
      sql += ' AND status = ?';
      params.push(status);
    }

    sql += ' ORDER BY date DESC, number DESC';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createJournalEntry: async (entry) => {
    const queries = [];
    
    // Insertar comprobante
    queries.push({
      sql: `
        INSERT INTO journal_entries (number, date, entry_type, description, 
          status, created_by, created_at, needs_sync)
        VALUES (?, ?, ?, ?, 'DRAFT', ?, datetime('now'), 1)
      `,
      params: [entry.number, entry.date, entry.entryType, entry.description, entry.createdBy]
    });

    // Insertar líneas
    entry.lines.forEach(line => {
      queries.push({
        sql: `
          INSERT INTO journal_entry_lines (journal_entry_id, account_id, 
            third_party_id, cost_center_id, description, debit, credit, 
            base_amount, needs_sync)
          VALUES (last_insert_rowid(), ?, ?, ?, ?, ?, ?, ?, 1)
        `,
        params: [
          line.accountId, line.thirdPartyId, line.costCenterId,
          line.description, line.debit, line.credit, line.baseAmount
        ]
      });
    });

    return ipcRenderer.invoke('db-transaction', queries);
  },

  postJournalEntry: async (id) => {
    const sql = `
      UPDATE journal_entries SET status = 'POSTED', 
        updated_at = datetime('now'), needs_sync = 1
      WHERE id = ?
    `;
    return ipcRenderer.invoke('db-query', sql, [id]);
  },

  // Third Parties (Terceros)
  getThirdParties: async (filters = {}) => {
    const { search, identification_type, person_type } = filters;
    let sql = 'SELECT * FROM third_parties WHERE 1=1';
    const params = [];

    if (search) {
      sql += ' AND (identification_number LIKE ? OR business_name LIKE ? OR trade_name LIKE ? OR first_name LIKE ? OR surname LIKE ?)';
      params.push(`%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`, `%${search}%`);
    }
    if (identification_type) {
      sql += ' AND identification_type = ?';
      params.push(identification_type);
    }
    if (person_type) {
      sql += ' AND person_type = ?';
      params.push(person_type);
    }

    sql += ' ORDER BY business_name, first_name';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createThirdParty: async (thirdParty) => {
    const sql = `
      INSERT INTO third_parties (
        party_type, person_type, identification_type, identification_number, check_digit,
        business_name, trade_name, first_name, middle_name, surname, second_surname,
        country_code, department_code, city_code, postal_code, address,
        tax_regime, fiscal_responsibilities, ciiu_code,
        phone, email, mobile, is_customer, is_supplier,
        created_at, needs_sync
      )
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
    `;
    
    // Convert array to string if necessary for SQLite
    const fiscalResp = Array.isArray(thirdParty.fiscal_responsibilities) 
      ? thirdParty.fiscal_responsibilities.join(',') 
      : thirdParty.fiscal_responsibilities;

    return ipcRenderer.invoke('db-query', sql, [
      thirdParty.party_type, thirdParty.person_type, thirdParty.identification_type, thirdParty.identification_number, thirdParty.check_digit,
      thirdParty.business_name, thirdParty.trade_name, thirdParty.first_name, thirdParty.middle_name, thirdParty.surname, thirdParty.second_surname,
      thirdParty.country_code, thirdParty.department_code, thirdParty.city_code, thirdParty.postal_code, thirdParty.address,
      thirdParty.tax_regime, fiscalResp, thirdParty.ciiu_code,
      thirdParty.phone, thirdParty.email, thirdParty.mobile, 
      thirdParty.is_customer ? 1 : 0, thirdParty.is_supplier ? 1 : 0
    ]);
  },

  // Electronic Documents (Documentos DIAN)
  getElectronicDocuments: async (filters = {}) => {
    const { startDate, endDate, documentType, status } = filters;
    let sql = 'SELECT * FROM electronic_documents WHERE 1=1';
    const params = [];

    if (startDate) {
      sql += ' AND issue_date >= ?';
      params.push(startDate);
    }
    if (endDate) {
      sql += ' AND issue_date <= ?';
      params.push(endDate);
    }
    if (documentType) {
      sql += ' AND document_type = ?';
      params.push(documentType);
    }
    if (status) {
      sql += ' AND status = ?';
      params.push(status);
    }

    sql += ' ORDER BY issue_date DESC, number DESC';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createElectronicDocument: async (document) => {
    const queries = [];
    
    // Insertar documento
    queries.push({
      sql: `
        INSERT INTO electronic_documents (document_type, prefix, number, 
          issue_date, customer_id, payment_method, payment_means, 
          payment_due_date, subtotal, total_tax, total, notes,
          status, created_at, needs_sync)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', datetime('now'), 1)
      `,
      params: [
        document.documentType, document.prefix, document.number,
        document.issueDate, document.customerId, document.paymentMethod,
        document.paymentMeans, document.paymentDueDate, document.subtotal,
        document.totalTax, document.total, document.notes
      ]
    });

    // Insertar líneas
    document.lines.forEach(line => {
      queries.push({
        sql: `
          INSERT INTO electronic_document_lines (electronic_document_id,
            line_number, product_code, description, quantity, unit,
            unit_price, subtotal, discount, needs_sync)
          VALUES (last_insert_rowid(), ?, ?, ?, ?, ?, ?, ?, ?, 1)
        `,
        params: [
          line.lineNumber, line.productCode, line.description, line.quantity,
          line.unit, line.unitPrice, line.subtotal, line.discount
        ]
      });
    });

    return ipcRenderer.invoke('db-transaction', queries);
  },

  // DIAN Formats (Medios Magnéticos)
  getDianFormats: async (filters = {}) => {
    let sql = 'SELECT * FROM dian_formats WHERE 1=1';
    const params = [];
    if (filters.search) {
       sql += ' AND (name LIKE ? OR code LIKE ?)';
       params.push(`%${filters.search}%`, `%${filters.search}%`);
    }
    sql += ' ORDER BY code';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createDianFormat: async (data) => {
    const sql = `INSERT INTO dian_formats (code, name, version, valid_from, server_id, needs_sync) VALUES (?, ?, ?, ?, ?, 1)`;
    return ipcRenderer.invoke('db-query', sql, [data.code, data.name, data.version, data.valid_from, null]);
  },
  
  updateDianFormat: async (id, data) => {
      const sql = 'UPDATE dian_formats SET code=?, name=?, version=?, valid_from=?, needs_sync=1 WHERE id=?';
      return ipcRenderer.invoke('db-query', sql, [data.code, data.name, data.version, data.valid_from, id]);
  },

  deleteDianFormat: async (id) => {
      // Primero eliminar conceptos asociados
      await ipcRenderer.invoke('db-query', 'DELETE FROM dian_concepts WHERE dian_format_id=?', [id]);
      return ipcRenderer.invoke('db-query', 'DELETE FROM dian_formats WHERE id=?', [id]);
  },

  // DIAN Concepts
  getDianConcepts: async (formatId) => {
    let sql = 'SELECT * FROM dian_concepts WHERE 1=1';
    const params = [];
    if (formatId) {
        sql += ' AND dian_format_id = ?';
        params.push(formatId);
    }
    sql += ' ORDER BY code';
    return ipcRenderer.invoke('db-query', sql, params);
  },

  createDianConcept: async (data) => {
      const sql = 'INSERT INTO dian_concepts (dian_format_id, code, name, description, server_id, needs_sync) VALUES (?, ?, ?, ?, ?, 1)';
      return ipcRenderer.invoke('db-query', sql, [data.dian_format, data.code, data.name, data.description, null]);
  },
  
  updateDianConcept: async (id, data) => {
      const sql = 'UPDATE dian_concepts SET dian_format_id=?, code=?, name=?, description=?, needs_sync=1 WHERE id=?';
      return ipcRenderer.invoke('db-query', sql, [data.dian_format, data.code, data.name, data.description, id]);
  },
  
  deleteDianConcept: async (id) => {
      return ipcRenderer.invoke('db-query', 'DELETE FROM dian_concepts WHERE id=?', [id]);
  }
});

console.log('✓ Preload script cargado correctamente');
