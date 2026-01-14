const Database = require('better-sqlite3');
const path = require('path');

// Ruta de la base de datos
const userDataPath = path.join(process.env.APPDATA, 'satori-desktop');
const dbPath = path.join(userDataPath, 'satori.db');

console.log('📂 Ruta de la base de datos:', dbPath);

const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

console.log('\n🔄 Cargando datos de prueba...');

let stats = {
  thirdParties: 0,
  journalEntries: 0,
  documents: 0
};

// 1. Cargar Terceros
console.log('\n📋 Cargando terceros...');
const thirdParties = [
  {
    id_type: 'NIT', id_number: '900123456', check_digit: '3',
    name: 'DISTRIBUIDORA NACIONAL S.A.S', trade_name: 'DISTRINACIONAL',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 1, is_supplier: 0,
    address: 'Calle 100 # 15-20', city: 'Bogotá',
    phone: '6012345678', email: 'ventas@distrinacional.com'
  },
  {
    id_type: 'NIT', id_number: '800234567', check_digit: '8',
    name: 'COMERCIALIZADORA DEL CARIBE LTDA', trade_name: 'COMCARIBE',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 1, is_supplier: 0,
    address: 'Carrera 50 # 80-45', city: 'Barranquilla',
    phone: '6053456789', email: 'info@comcaribe.com'
  },
  {
    id_type: 'NIT', id_number: '700345678', check_digit: '1',
    name: 'INVERSIONES ANTIOQUIA S.A', trade_name: 'INVERANTIOQUIA',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 1, is_supplier: 0,
    address: 'Avenida Oriental # 40-12', city: 'Medellín',
    phone: '6044567890', email: 'clientes@inverantioquia.com'
  },
  {
    id_type: 'NIT', id_number: '600456789', check_digit: '5',
    name: 'PROVEEDORA DE INSUMOS S.A.S', trade_name: 'PROINSUMOS',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 0, is_supplier: 1,
    address: 'Calle 45 # 30-15', city: 'Bogotá',
    phone: '6015678901', email: 'ventas@proinsumos.com'
  },
  {
    id_type: 'NIT', id_number: '500567890', check_digit: '9',
    name: 'SUMINISTROS INDUSTRIALES LTDA', trade_name: 'SUMIND',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 0, is_supplier: 1,
    address: 'Carrera 70 # 25-80', city: 'Cali',
    phone: '6026789012', email: 'compras@sumind.com'
  },
  {
    id_type: 'CC', id_number: '1234567890', check_digit: null,
    name: 'JUAN CARLOS RODRIGUEZ MARTINEZ', trade_name: null,
    person_type: 'NATURAL', tax_regime: 'SIMPLIFICADO',
    is_customer: 1, is_supplier: 0,
    address: 'Calle 20 # 10-30', city: 'Bogotá',
    phone: '3101234567', email: 'jcrodriguez@email.com'
  },
  {
    id_type: 'CC', id_number: '9876543210', check_digit: null,
    name: 'MARIA FERNANDA GOMEZ SILVA', trade_name: null,
    person_type: 'NATURAL', tax_regime: 'SIMPLIFICADO',
    is_customer: 1, is_supplier: 0,
    address: 'Carrera 15 # 85-40', city: 'Medellín',
    phone: '3209876543', email: 'mfgomez@email.com'
  },
  {
    id_type: 'NIT', id_number: '400678901', check_digit: '2',
    name: 'SERVICIOS CONTABLES Y AUDITORIA S.A.S', trade_name: 'SERCONTAUD',
    person_type: 'JURIDICA', tax_regime: 'COMUN',
    is_customer: 0, is_supplier: 1,
    address: 'Avenida 19 # 100-50', city: 'Bogotá',
    phone: '6017890123', email: 'contacto@sercontaud.com'
  }
];

const checkThirdParty = db.prepare('SELECT id FROM third_parties WHERE id_number = ?');
const insertThirdParty = db.prepare(`
  INSERT INTO third_parties (
    id_type, id_number, check_digit, name, trade_name, person_type, tax_regime,
    is_customer, is_supplier, address, city, phone, email,
    created_at, updated_at, is_synced
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
`);

for (const tp of thirdParties) {
  const existing = checkThirdParty.get(tp.id_number);
  if (!existing) {
    insertThirdParty.run(
      tp.id_type, tp.id_number, tp.check_digit, tp.name, tp.trade_name,
      tp.person_type, tp.tax_regime, tp.is_customer, tp.is_supplier,
      tp.address, tp.city, tp.phone, tp.email
    );
    stats.thirdParties++;
  }
}

console.log(`✅ Terceros insertados: ${stats.thirdParties}`);

// 2. Cargar Comprobantes
console.log('\n📊 Cargando comprobantes contables...');

const insertJournalEntry = db.prepare(`
  INSERT INTO journal_entries (
    number, date, entry_type, description, status,
    created_at, updated_at, is_synced
  ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
`);

const insertJournalLine = db.prepare(`
  INSERT INTO journal_entry_lines (
    journal_entry_id, account_id, third_party_id, description, debit, credit,
    created_at, updated_at, is_synced
  ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
`);

const getAccount = db.prepare('SELECT id FROM accounts WHERE code = ? LIMIT 1');
const getThirdParty = db.prepare('SELECT id FROM third_parties WHERE id_number = ? LIMIT 1');

// Comprobante de Apertura
const apertura = insertJournalEntry.run('CE-001', '2026-01-01', 'APERTURA', 'Comprobante de apertura año 2026', 'POSTED');
const acc110505 = getAccount.get('110505');
const acc111005 = getAccount.get('111005');
const acc310505 = getAccount.get('310505');

if (acc110505 && acc111005 && acc310505) {
  insertJournalLine.run(apertura.lastInsertRowid, acc110505.id, null, 'Saldo inicial Caja General', 5000000, 0);
  insertJournalLine.run(apertura.lastInsertRowid, acc111005.id, null, 'Saldo inicial Banco Nacional', 50000000, 0);
  insertJournalLine.run(apertura.lastInsertRowid, acc310505.id, null, 'Capital inicial', 0, 55000000);
  stats.journalEntries++;
}

// Comprobante de Compra
const compra = insertJournalEntry.run('CE-002', '2026-01-05', 'DIARIO', 'Compra de mercancía PROINSUMOS', 'POSTED');
const acc143505 = getAccount.get('143505');
const acc240805 = getAccount.get('240805');
const acc220505 = getAccount.get('220505');
const proveedorProinsumos = getThirdParty.get('600456789');

if (acc143505 && acc240805 && acc220505 && proveedorProinsumos) {
  insertJournalLine.run(compra.lastInsertRowid, acc143505.id, null, 'Compra mercancía para reventa', 10000000, 0);
  insertJournalLine.run(compra.lastInsertRowid, acc240805.id, null, 'IVA por pagar', 1900000, 0);
  insertJournalLine.run(compra.lastInsertRowid, acc220505.id, proveedorProinsumos.id, 'Proveedor PROINSUMOS', 0, 11900000);
  stats.journalEntries++;
}

// Comprobante de Gastos
const gastos = insertJournalEntry.run('CE-003', '2026-01-08', 'DIARIO', 'Pago de servicios públicos y arriendo', 'POSTED');
const acc513505 = getAccount.get('513505');
const acc512005 = getAccount.get('512005');

if (acc513505 && acc512005 && acc111005) {
  insertJournalLine.run(gastos.lastInsertRowid, acc513505.id, null, 'Energía eléctrica', 500000, 0);
  insertJournalLine.run(gastos.lastInsertRowid, acc512005.id, null, 'Arriendo oficina', 2000000, 0);
  insertJournalLine.run(gastos.lastInsertRowid, acc111005.id, null, 'Pago desde banco', 0, 2500000);
  stats.journalEntries++;
}

console.log(`✅ Comprobantes insertados: ${stats.journalEntries}`);

// 3. Cargar Facturas
console.log('\n📄 Cargando facturas electrónicas...');

const customers = db.prepare('SELECT id FROM third_parties WHERE is_customer = 1 LIMIT 3').all();

if (customers.length > 0) {
  const insertDoc = db.prepare(`
    INSERT INTO electronic_documents (
      document_type, prefix, number, issue_date, customer_id, payment_method, payment_means,
      subtotal, tax_total, total, status, cufe,
      created_at, updated_at, is_synced
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
  `);
  
  const insertLine = db.prepare(`
    INSERT INTO electronic_document_lines (
      electronic_document_id, line_number, product_code, description,
      quantity, unit_price, discount, line_total,
      created_at, updated_at, is_synced
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
  `);
  
  const insertTax = db.prepare(`
    INSERT INTO electronic_document_taxes (
      electronic_document_id, tax_category, tax_rate, taxable_amount, tax_amount,
      created_at, updated_at, is_synced
    ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
  `);
  
  // Factura 1
  const fac1 = insertDoc.run('INVOICE', 'SEFE', '00001', '2026-01-10', customers[0].id, 'CREDITO', 'TRANSFERENCIA',
    5000000, 950000, 5950000, 'SENT', 'CUFE123456789ABCDEF');
  insertLine.run(fac1.lastInsertRowid, 1, 'PROD-001', 'Producto A - Alta calidad', 10, 300000, 0, 3000000);
  insertLine.run(fac1.lastInsertRowid, 2, 'PROD-002', 'Producto B - Premium', 5, 400000, 0, 2000000);
  insertTax.run(fac1.lastInsertRowid, 'IVA', 19, 5000000, 950000);
  stats.documents++;
  
  // Factura 2
  if (customers.length > 1) {
    const fac2 = insertDoc.run('INVOICE', 'SEFE', '00002', '2026-01-10', customers[1].id, 'CREDITO', 'TRANSFERENCIA',
      8000000, 1520000, 9520000, 'SENT', 'CUFE987654321FEDCBA');
    insertLine.run(fac2.lastInsertRowid, 1, 'PROD-003', 'Producto C - Estándar', 20, 400000, 0, 8000000);
    insertTax.run(fac2.lastInsertRowid, 'IVA', 19, 8000000, 1520000);
    stats.documents++;
  }
}

console.log(`✅ Facturas insertadas: ${stats.documents}`);

console.log('\n✅ Carga de datos de prueba completada:');
console.log(`   📋 Terceros: ${stats.thirdParties}`);
console.log(`   📊 Comprobantes: ${stats.journalEntries}`);
console.log(`   📄 Facturas: ${stats.documents}`);

db.close();
console.log('\n✅ Base de datos cerrada correctamente');
