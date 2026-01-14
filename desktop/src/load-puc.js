const fs = require('fs');
const path = require('path');

class PUCLoader {
  constructor(database) {
    this.db = database;
  }

  async loadPUC() {
    try {
      console.log('🔄 Iniciando carga del PUC colombiano...');
      
      // Leer el archivo JSON
      const pucFilePath = path.join(__dirname, 'puc-data.json');
      const pucData = JSON.parse(fs.readFileSync(pucFilePath, 'utf8'));
      
      console.log(`📊 Total de cuentas a cargar: ${pucData.length}`);
      
      // Verificar si ya hay datos
      const existingAccounts = this.db.query('SELECT COUNT(*) as count FROM accounts');
      
      if (existingAccounts[0].count > 0) {
        console.log(`⚠️  Ya existen ${existingAccounts[0].count} cuentas en la base de datos.`);
        console.log('¿Desea continuar y agregar las nuevas cuentas? (Se omitirán duplicados)');
      }
      
      let inserted = 0;
      let skipped = 0;
      let errors = 0;
      
      // Insertar cada cuenta
      for (const account of pucData) {
        try {
          // Verificar si la cuenta ya existe
          const existing = this.db.query(
            'SELECT id FROM accounts WHERE code = ?',
            [account.code]
          );
          
          if (existing.length > 0) {
            skipped++;
            continue;
          }
          
          // Insertar la cuenta
          this.db.run(
            `INSERT INTO accounts (
              code, name, level, account_type, nature,
              allows_movement, requires_third_party, requires_cost_center, is_tax_account,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))`,
            [
              account.code,
              account.name,
              account.level,
              account.account_type,
              account.nature,
              account.allows_movement ? 1 : 0,
              account.requires_third_party ? 1 : 0,
              account.requires_cost_center ? 1 : 0,
              account.is_tax_account ? 1 : 0
            ]
          );
          
          inserted++;
          
          // Mostrar progreso cada 50 registros
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
      
      // Verificar total final
      const finalCount = this.db.query('SELECT COUNT(*) as count FROM accounts');
      console.log(`\n📊 Total de cuentas en la base de datos: ${finalCount[0].count}`);
      
      return {
        inserted,
        skipped,
        errors,
        total: finalCount[0].count
      };
      
    } catch (error) {
      console.error('❌ Error fatal al cargar el PUC:', error);
      throw error;
    }
  }
  
  async clearAccounts() {
    try {
      console.log('🗑️  Eliminando todas las cuentas...');
      this.db.run('DELETE FROM accounts');
      console.log('✅ Todas las cuentas han sido eliminadas.');
    } catch (error) {
      console.error('❌ Error al eliminar cuentas:', error);
      throw error;
    }
  }
}

// Si se ejecuta directamente desde la línea de comandos
if (require.main === module) {
  const loader = new PUCLoader();
  
  const args = process.argv.slice(2);
  
  if (args.includes('--clear')) {
    loader.clearAccounts()
      .then(() => process.exit(0))
      .catch(err => {
        console.error(err);
        process.exit(1);
      });
  } else {
    loader.loadPUC()
      .then(() => process.exit(0))
      .catch(err => {
        console.error(err);
        process.exit(1);
      });
  }
}

module.exports = PUCLoader;
