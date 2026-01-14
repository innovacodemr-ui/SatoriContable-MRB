const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

// Ruta de la base de datos
const userDataPath = path.join(process.env.APPDATA, 'satori-desktop');
const dbPath = path.join(userDataPath, 'satori.db');

console.log('📂 Ruta de la base de datos:', dbPath);

// Asegurar que existe el directorio
if (!fs.existsSync(userDataPath)) {
  fs.mkdirSync(userDataPath, { recursive: true });
}

// Conectar a la base de datos
const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

console.log('\n🔄 Iniciando carga del PUC colombiano...');

// Leer el archivo JSON
const pucFilePath = path.join(__dirname, 'puc-data.json');
const pucData = JSON.parse(fs.readFileSync(pucFilePath, 'utf8'));

console.log(`📊 Total de cuentas a cargar: ${pucData.length}`);

// Verificar si ya hay datos
const existingAccounts = db.prepare('SELECT COUNT(*) as count FROM accounts').get();

if (existingAccounts.count > 0) {
  console.log(`⚠️  Ya existen ${existingAccounts.count} cuentas en la base de datos.`);
}

let inserted = 0;
let skipped = 0;
let errors = 0;

// Preparar la consulta de inserción
const insertStmt = db.prepare(`
  INSERT INTO accounts (
    code, name, level, account_type, nature,
    allows_movement, requires_third_party, requires_cost_center, is_tax_account,
    created_at, updated_at, is_synced
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
`);

const checkStmt = db.prepare('SELECT id FROM accounts WHERE code = ?');

// Insertar cada cuenta
for (const account of pucData) {
  try {
    const existing = checkStmt.get(account.code);
    
    if (existing) {
      skipped++;
      continue;
    }
    
    insertStmt.run(
      account.code,
      account.name,
      account.level,
      account.account_type,
      account.nature,
      account.allows_movement ? 1 : 0,
      account.requires_third_party ? 1 : 0,
      account.requires_cost_center ? 1 : 0,
      account.is_tax_account ? 1 : 0
    );
    
    inserted++;
    
    if (inserted % 50 === 0) {
      console.log(`   Procesadas ${inserted + skipped} de ${pucData.length}...`);
    }
    
  } catch (error) {
    errors++;
    console.error(`❌ Error al insertar cuenta ${account.code}:`, error.message);
  }
}

console.log('\n✅ Carga del PUC completada:');
console.log(`   ✓ Insertadas: ${inserted}`);
console.log(`   ⊘ Omitidas (duplicadas): ${skipped}`);
console.log(`   ✗ Errores: ${errors}`);

const finalCount = db.prepare('SELECT COUNT(*) as count FROM accounts').get();
console.log(`\n📊 Total de cuentas en la base de datos: ${finalCount.count}`);

db.close();
console.log('\n✅ Base de datos cerrada correctamente');
