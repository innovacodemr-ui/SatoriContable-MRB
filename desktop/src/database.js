/**
 * Gestor de base de datos SQLite para Electron
 */

const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');

class LocalDatabase {
  constructor() {
    // Ruta de la base de datos en el directorio de datos del usuario
    const userDataPath = app.getPath('userData');
    this.dbPath = path.join(userDataPath, 'satori.db');
    this.db = null;
  }

  /**
   * Inicializar base de datos
   */
  async initialize() {
    try {
      // Crear conexión
      this.db = new Database(this.dbPath);
      
      // Configurar modo WAL para mejor rendimiento
      this.db.pragma('journal_mode = WAL');
      this.db.pragma('synchronous = NORMAL');
      
      // Crear tablas si no existen
      await this.createTables();
      
      console.log(`✓ Base de datos inicializada: ${this.dbPath}`);
      return true;
    } catch (error) {
      console.error('Error al inicializar base de datos:', error);
      throw error;
    }
  }

  /**
   * Crear estructura de tablas
   */
  async createTables() {
    const schema = `
      -- Usuarios
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        is_active INTEGER DEFAULT 1,
        is_staff INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT
      );

      -- Clases de cuenta (PUC Nivel 1)
      CREATE TABLE IF NOT EXISTS account_classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER
      );

      -- Grupos de cuenta (PUC Nivel 2)
      CREATE TABLE IF NOT EXISTS account_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        account_class_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (account_class_id) REFERENCES account_classes(id)
      );

      -- Cuentas (PUC Niveles 3-6)
      CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        level INTEGER NOT NULL,
        nature TEXT NOT NULL CHECK(nature IN ('DEBITO', 'CREDITO')),
        account_type TEXT NOT NULL CHECK(account_type IN ('ACTIVO', 'PASIVO', 'PATRIMONIO', 'INGRESO', 'GASTO', 'COSTO')),
        allows_movement INTEGER DEFAULT 1,
        requires_third_party INTEGER DEFAULT 0,
        requires_cost_center INTEGER DEFAULT 0,
        is_tax_account INTEGER DEFAULT 0,
        tax_type TEXT,
        
        -- Relación DIAN
        dian_format_id INTEGER,
        dian_concept_id INTEGER,
        
        parent_id INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES accounts(id),
        FOREIGN KEY (dian_format_id) REFERENCES dian_formats(id),
        FOREIGN KEY (dian_concept_id) REFERENCES dian_concepts(id)
      );

      -- Formatos DIAN (Exógena)
      CREATE TABLE IF NOT EXISTS dian_formats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        version INTEGER DEFAULT 1,
        valid_from INTEGER,
        server_id INTEGER,
        UNIQUE(code, version, valid_from)
      );

      -- Conceptos DIAN
      CREATE TABLE IF NOT EXISTS dian_concepts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dian_format_id INTEGER NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        server_id INTEGER,
        FOREIGN KEY (dian_format_id) REFERENCES dian_formats(id),
        UNIQUE(dian_format_id, code)
      );

      -- Centros de costo
      CREATE TABLE IF NOT EXISTS cost_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER
      );

      -- Terceros (clientes/proveedores)
      CREATE TABLE IF NOT EXISTS third_parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        party_type TEXT DEFAULT 'CLIENTE', -- 'CLIENTE', 'PROVEEDOR', 'EMPLEADO', 'SOCIO', 'OTRO'
        person_type INTEGER DEFAULT 1, -- 1: Juridica, 2: Natural
        identification_type TEXT NOT NULL, -- '13', '31', '21', '22', '42', '50', '91', etc.
        identification_number TEXT NOT NULL,
        check_digit TEXT,
        
        business_name TEXT,
        trade_name TEXT,
        first_name TEXT,
        middle_name TEXT,
        surname TEXT,
        second_surname TEXT,
        
        country_code TEXT DEFAULT 'CO',
        department_code TEXT,
        city_code TEXT,
        postal_code TEXT,
        address TEXT,
        
        tax_regime TEXT, -- '48', '49', '42'
        fiscal_responsibilities TEXT, -- JSON o texto separado por comas
        ciiu_code TEXT,
        
        phone TEXT,
        email TEXT,
        mobile TEXT,
        
        is_customer INTEGER DEFAULT 0,
        is_supplier INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        UNIQUE(identification_type, identification_number)
      );

      -- Comprobantes contables
      CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL,
        date TEXT NOT NULL,
        entry_type TEXT NOT NULL CHECK(entry_type IN ('APERTURA', 'DIARIO', 'AJUSTE', 'CIERRE', 'NOTA')),
        description TEXT,
        status TEXT DEFAULT 'DRAFT' CHECK(status IN ('DRAFT', 'POSTED', 'CANCELLED')),
        created_by INTEGER,
        posted_by INTEGER,
        posted_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (created_by) REFERENCES users(id),
        FOREIGN KEY (posted_by) REFERENCES users(id)
      );

      -- Líneas de comprobantes
      CREATE TABLE IF NOT EXISTS journal_entry_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        journal_entry_id INTEGER NOT NULL,
        account_id INTEGER NOT NULL,
        third_party_id INTEGER,
        cost_center_id INTEGER,
        description TEXT,
        debit REAL DEFAULT 0,
        credit REAL DEFAULT 0,
        base_amount REAL DEFAULT 0,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES accounts(id),
        FOREIGN KEY (third_party_id) REFERENCES third_parties(id),
        FOREIGN KEY (cost_center_id) REFERENCES cost_centers(id)
      );

      -- Resoluciones DIAN
      CREATE TABLE IF NOT EXISTS dian_resolutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resolution_number TEXT NOT NULL,
        prefix TEXT NOT NULL,
        start_number INTEGER NOT NULL,
        end_number INTEGER NOT NULL,
        current_number INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        technical_key TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER
      );

      -- Documentos electrónicos DIAN
      CREATE TABLE IF NOT EXISTS electronic_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_type TEXT NOT NULL CHECK(document_type IN ('INVOICE', 'CREDIT_NOTE', 'DEBIT_NOTE', 'PAYROLL', 'SUPPORT_DOCUMENT')),
        prefix TEXT NOT NULL,
        number INTEGER NOT NULL,
        issue_date TEXT NOT NULL,
        customer_id INTEGER NOT NULL,
        payment_method TEXT,
        payment_means TEXT,
        payment_due_date TEXT,
        subtotal REAL NOT NULL,
        total_tax REAL NOT NULL,
        total REAL NOT NULL,
        notes TEXT,
        cufe TEXT,
        qr_code TEXT,
        status TEXT DEFAULT 'DRAFT' CHECK(status IN ('DRAFT', 'PENDING', 'SENT', 'ACCEPTED', 'REJECTED', 'CANCELLED')),
        xml_file TEXT,
        pdf_file TEXT,
        dian_response TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (customer_id) REFERENCES third_parties(id),
        UNIQUE(prefix, number)
      );

      -- Líneas de documentos electrónicos
      CREATE TABLE IF NOT EXISTS electronic_document_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        electronic_document_id INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        product_code TEXT,
        description TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        unit_price REAL NOT NULL,
        subtotal REAL NOT NULL,
        discount REAL DEFAULT 0,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (electronic_document_id) REFERENCES electronic_documents(id) ON DELETE CASCADE
      );

      -- Impuestos de documentos electrónicos
      CREATE TABLE IF NOT EXISTS electronic_document_taxes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        electronic_document_id INTEGER NOT NULL,
        line_id INTEGER,
        tax_category TEXT NOT NULL,
        tax_rate REAL NOT NULL,
        taxable_amount REAL NOT NULL,
        tax_amount REAL NOT NULL,
        needs_sync INTEGER DEFAULT 0,
        server_id INTEGER,
        FOREIGN KEY (electronic_document_id) REFERENCES electronic_documents(id) ON DELETE CASCADE,
        FOREIGN KEY (line_id) REFERENCES electronic_document_lines(id)
      );

      -- Log de sincronización
      CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_type TEXT NOT NULL CHECK(sync_type IN ('PUSH', 'PULL', 'FULL')),
        status TEXT NOT NULL CHECK(status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
        records_sent INTEGER DEFAULT 0,
        records_received INTEGER DEFAULT 0,
        records_failed INTEGER DEFAULT 0,
        error_message TEXT,
        started_at TEXT DEFAULT CURRENT_TIMESTAMP,
        completed_at TEXT
      );

      -- Índices para mejorar rendimiento
      CREATE INDEX IF NOT EXISTS idx_accounts_code ON accounts(code);
      CREATE INDEX IF NOT EXISTS idx_accounts_parent ON accounts(parent_id);
      CREATE INDEX IF NOT EXISTS idx_third_parties_id_number ON third_parties(id_number);
      CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(date);
      CREATE INDEX IF NOT EXISTS idx_journal_entries_status ON journal_entries(status);
      CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_journal ON journal_entry_lines(journal_entry_id);
      CREATE INDEX IF NOT EXISTS idx_electronic_documents_date ON electronic_documents(issue_date);
      CREATE INDEX IF NOT EXISTS idx_electronic_documents_status ON electronic_documents(status);
      CREATE INDEX IF NOT EXISTS idx_sync_needs ON accounts(needs_sync);
    `;

    // Ejecutar todas las sentencias del schema
    this.db.exec(schema);
  }

  /**
   * Ejecutar consulta SELECT
   */
  query(sql, params = []) {
    try {
      const stmt = this.db.prepare(sql);
      return stmt.all(...params);
    } catch (error) {
      console.error('Error en query:', error);
      throw error;
    }
  }

  /**
   * Ejecutar consulta INSERT/UPDATE/DELETE
   */
  run(sql, params = []) {
    try {
      const stmt = this.db.prepare(sql);
      return stmt.run(...params);
    } catch (error) {
      console.error('Error en run:', error);
      throw error;
    }
  }

  /**
   * Ejecutar transacción
   */
  transaction(queries) {
    const transaction = this.db.transaction(() => {
      const results = [];
      for (const query of queries) {
        const stmt = this.db.prepare(query.sql);
        results.push(stmt.run(...query.params));
      }
      return results;
    });

    try {
      return transaction();
    } catch (error) {
      console.error('Error en transacción:', error);
      throw error;
    }
  }

  /**
   * Obtener registros que necesitan sincronización
   */
  getPendingSync() {
    const tables = [
      'accounts', 'third_parties', 'journal_entries', 
      'dian_formats', 'dian_concepts',
      'journal_entry_lines', 'electronic_documents',
      'electronic_document_lines', 'electronic_document_taxes'
    ];

    const pending = {};
    
    for (const table of tables) {
      const records = this.query(
        `SELECT * FROM ${table} WHERE needs_sync = 1`
      );
      if (records.length > 0) {
        pending[table] = records;
      }
    }

    return pending;
  }

  /**
   * Marcar registros como sincronizados
   */
  markAsSynced(table, ids) {
    if (ids.length === 0) return;
    
    const placeholders = ids.map(() => '?').join(',');
    const sql = `UPDATE ${table} SET needs_sync = 0 WHERE id IN (${placeholders})`;
    return this.run(sql, ids);
  }

  /**
   * Cerrar conexión
   */
  close() {
    if (this.db) {
      this.db.close();
      console.log('✓ Base de datos cerrada');
    }
  }

  /**
   * Hacer backup de la base de datos
   */
  backup(destinationPath) {
    try {
      const backup = this.db.backup(destinationPath);
      backup.step(-1); // Copiar todo
      backup.finish();
      console.log(`✓ Backup creado: ${destinationPath}`);
      return true;
    } catch (error) {
      console.error('Error al crear backup:', error);
      throw error;
    }
  }

  /**
   * Obtener estadísticas de la base de datos
   */
  getStats() {
    return {
      accounts: this.query('SELECT COUNT(*) as count FROM accounts')[0].count,
      thirdParties: this.query('SELECT COUNT(*) as count FROM third_parties')[0].count,
      journalEntries: this.query('SELECT COUNT(*) as count FROM journal_entries')[0].count,
      electronicDocuments: this.query('SELECT COUNT(*) as count FROM electronic_documents')[0].count,
      pendingSync: this.query('SELECT COUNT(*) as count FROM accounts WHERE needs_sync = 1')[0].count +
                    this.query('SELECT COUNT(*) as count FROM third_parties WHERE needs_sync = 1')[0].count +
                    this.query('SELECT COUNT(*) as count FROM journal_entries WHERE needs_sync = 1')[0].count
    };
  }
}

module.exports = LocalDatabase;
