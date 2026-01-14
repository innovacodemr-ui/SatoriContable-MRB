class TestDataLoader {
  constructor(database) {
    this.db = database;
  }

  async loadTestData() {
    try {
      console.log('🔄 Cargando datos de prueba...');

      // Verificar si ya hay datos
      const existingThirdParties = this.db.query('SELECT COUNT(*) as count FROM third_parties');
      if (existingThirdParties[0].count > 0) {
        console.log('⚠️  Ya existen datos. Se omitirán duplicados.');
      }

      let stats = {
        thirdParties: 0,
        journalEntries: 0,
        documents: 0
      };

      // 1. Cargar Terceros (Clientes y Proveedores)
      console.log('\n📋 Cargando terceros...');
      const thirdParties = [
        {
          id_type: 'NIT',
          id_number: '900123456',
          check_digit: '3',
          name: 'DISTRIBUIDORA NACIONAL S.A.S',
          trade_name: 'DISTRINACIONAL',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: true,
          is_supplier: false,
          address: 'Calle 100 # 15-20',
          city: 'Bogotá',
          phone: '6012345678',
          email: 'ventas@distrinacional.com'
        },
        {
          id_type: 'NIT',
          id_number: '800234567',
          check_digit: '8',
          name: 'COMERCIALIZADORA DEL CARIBE LTDA',
          trade_name: 'COMCARIBE',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: true,
          is_supplier: false,
          address: 'Carrera 50 # 80-45',
          city: 'Barranquilla',
          phone: '6053456789',
          email: 'info@comcaribe.com'
        },
        {
          id_type: 'NIT',
          id_number: '700345678',
          check_digit: '1',
          name: 'INVERSIONES ANTIOQUIA S.A',
          trade_name: 'INVERANTIOQUIA',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: true,
          is_supplier: false,
          address: 'Avenida Oriental # 40-12',
          city: 'Medellín',
          phone: '6044567890',
          email: 'clientes@inverantioquia.com'
        },
        {
          id_type: 'NIT',
          id_number: '600456789',
          check_digit: '5',
          name: 'PROVEEDORA DE INSUMOS S.A.S',
          trade_name: 'PROINSUMOS',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: false,
          is_supplier: true,
          address: 'Calle 45 # 30-15',
          city: 'Bogotá',
          phone: '6015678901',
          email: 'ventas@proinsumos.com'
        },
        {
          id_type: 'NIT',
          id_number: '500567890',
          check_digit: '9',
          name: 'SUMINISTROS INDUSTRIALES LTDA',
          trade_name: 'SUMIND',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: false,
          is_supplier: true,
          address: 'Carrera 70 # 25-80',
          city: 'Cali',
          phone: '6026789012',
          email: 'compras@sumind.com'
        },
        {
          id_type: 'CC',
          id_number: '1234567890',
          check_digit: null,
          name: 'JUAN CARLOS RODRIGUEZ MARTINEZ',
          trade_name: null,
          person_type: 'NATURAL',
          tax_regime: 'SIMPLIFICADO',
          is_customer: true,
          is_supplier: false,
          address: 'Calle 20 # 10-30',
          city: 'Bogotá',
          phone: '3101234567',
          email: 'jcrodriguez@email.com'
        },
        {
          id_type: 'CC',
          id_number: '9876543210',
          check_digit: null,
          name: 'MARIA FERNANDA GOMEZ SILVA',
          trade_name: null,
          person_type: 'NATURAL',
          tax_regime: 'SIMPLIFICADO',
          is_customer: true,
          is_supplier: false,
          address: 'Carrera 15 # 85-40',
          city: 'Medellín',
          phone: '3209876543',
          email: 'mfgomez@email.com'
        },
        {
          id_type: 'NIT',
          id_number: '400678901',
          check_digit: '2',
          name: 'SERVICIOS CONTABLES Y AUDITORIA S.A.S',
          trade_name: 'SERCONTAUD',
          person_type: 'JURIDICA',
          tax_regime: 'COMUN',
          is_customer: false,
          is_supplier: true,
          address: 'Avenida 19 # 100-50',
          city: 'Bogotá',
          phone: '6017890123',
          email: 'contacto@sercontaud.com'
        }
      ];

      for (const tp of thirdParties) {
        try {
          const existing = this.db.query('SELECT id FROM third_parties WHERE id_number = ?', [tp.id_number]);
          if (existing.length === 0) {
            this.db.run(
              `INSERT INTO third_parties (
                id_type, id_number, check_digit, name, trade_name, person_type, tax_regime,
                is_customer, is_supplier, address, city, phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
              [
                tp.id_type, tp.id_number, tp.check_digit, tp.name, tp.trade_name, tp.person_type, tp.tax_regime,
                tp.is_customer ? 1 : 0, tp.is_supplier ? 1 : 0, tp.address, tp.city, tp.phone, tp.email
              ]
            );
            stats.thirdParties++;
          }
        } catch (error) {
          console.error(`Error al insertar tercero ${tp.name}:`, error.message);
        }
      }

      console.log(`✅ Terceros insertados: ${stats.thirdParties}`);

      // 2. Cargar Comprobantes Contables
      console.log('\n📊 Cargando comprobantes contables...');
      
      // Helper para obtener IDs de cuentas
      const getAccountId = (code) => {
        const account = this.db.query('SELECT id FROM accounts WHERE code = ? LIMIT 1', [code]);
        return account.length > 0 ? account[0].id : null;
      };
      
      // Comprobante de Apertura
      const apertura = this.db.run(
        `INSERT INTO journal_entries (
          number, date, entry_type, description, status) VALUES (?, ?, ?, ?, ?)`,
        ['CE-001', '2026-01-01', 'APERTURA', 'Comprobante de apertura año 2026', 'POSTED']
      );
      
      // Líneas del comprobante de apertura
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [apertura.lastInsertRowid, getAccountId('110505'), 'Saldo inicial Caja General', 5000000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [apertura.lastInsertRowid, getAccountId('111005'), 'Saldo inicial Banco Nacional', 50000000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [apertura.lastInsertRowid, getAccountId('310505'), 'Capital inicial', 0, 55000000]
      );
      
      stats.journalEntries++;

      // Comprobante de Compra
      const compra = this.db.run(
        `INSERT INTO journal_entries (
          number, date, entry_type, description, status) VALUES (?, ?, ?, ?, ?)`,
        ['CE-002', '2026-01-05', 'DIARIO', 'Compra de mercancía PROINSUMOS', 'POSTED']
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [compra.lastInsertRowid, getAccountId('143505'), 'Compra mercancía para reventa', 10000000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [compra.lastInsertRowid, getAccountId('240805'), 'IVA compras 19%', 1900000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [compra.lastInsertRowid, getAccountId('220505'), 'Proveedor PROINSUMOS', 0, 11900000]
      );
      
      stats.journalEntries++;

      // Comprobante de Gastos
      const gastos = this.db.run(
        `INSERT INTO journal_entries (
          number, date, entry_type, description, status) VALUES (?, ?, ?, ?, ?)`,
        ['CE-003', '2026-01-08', 'DIARIO', 'Pago de servicios públicos y arriendo', 'POSTED']
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [gastos.lastInsertRowid, getAccountId('513505'), 'Energía eléctrica', 500000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [gastos.lastInsertRowid, getAccountId('512005'), 'Arriendo local comercial', 2000000, 0]
      );
      
      this.db.run(
        `INSERT INTO journal_entry_lines (
          journal_entry_id, account_id, description, debit, credit) VALUES (?, ?, ?, ?, ?)`,
        [gastos.lastInsertRowid, getAccountId('111005'), 'Pago desde banco', 0, 2500000]
      );
      
      stats.journalEntries++;

      console.log(`✅ Comprobantes insertados: ${stats.journalEntries}`);

      // 3. Cargar Facturas Electrónicas
      console.log('\n📄 Cargando facturas electrónicas...');
      
      const customers = this.db.query('SELECT id FROM third_parties WHERE is_customer = 1 LIMIT 3');
      
      if (customers.length > 0) {
        // Factura 1
        const factura1 = this.db.run(
          `INSERT INTO electronic_documents (
            document_type, prefix, number, issue_date, customer_id, payment_method, payment_means,
            subtotal, total_tax, total, status, cufe) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          ['INVOICE', 'SEFE', '00001', '2026-01-10', customers[0].id, 'CONTADO', 'EFECTIVO',
           5000000, 950000, 5950000, 'SENT', 'CUFE123456789ABCDEF']
        );
        
        this.db.run(
          `INSERT INTO electronic_document_lines (
            electronic_document_id, line_number, product_code, description,
            quantity, unit, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [factura1.lastInsertRowid, 1, 'PROD-001', 'Producto A - Alta calidad', 10, 'UND', 300000, 0, 3000000]
        );
        
        this.db.run(
          `INSERT INTO electronic_document_lines (
            electronic_document_id, line_number, product_code, description,
            quantity, unit, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [factura1.lastInsertRowid, 2, 'PROD-002', 'Producto B - Premium', 5, 'UND', 400000, 0, 2000000]
        );
        
        this.db.run(
          `INSERT INTO electronic_document_taxes (
            electronic_document_id, tax_category, tax_rate, taxable_amount, tax_amount) VALUES (?, ?, ?, ?, ?)`,
          [factura1.lastInsertRowid, 'IVA', 19, 5000000, 950000]
        );
        
        stats.documents++;

        // Factura 2
        if (customers.length > 1) {
          const factura2 = this.db.run(
            `INSERT INTO electronic_documents (
              document_type, prefix, number, issue_date, customer_id, payment_method, payment_means,
              subtotal, total_tax, total, status, cufe) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            ['INVOICE', 'SEFE', '00002', '2026-01-10', customers[1].id, 'CREDITO', 'TRANSFERENCIA',
             8000000, 1520000, 9520000, 'SENT', 'CUFE987654321FEDCBA']
          );
          
          this.db.run(
            `INSERT INTO electronic_document_lines (
              electronic_document_id, line_number, product_code, description,
              quantity, unit, unit_price, discount, subtotal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            [factura2.lastInsertRowid, 1, 'PROD-003', 'Producto C - Estándar', 20, 'UND', 400000, 0, 8000000]
          );
          
          this.db.run(
            `INSERT INTO electronic_document_taxes (
              electronic_document_id, tax_category, tax_rate, taxable_amount, tax_amount) VALUES (?, ?, ?, ?, ?)`,
            [factura2.lastInsertRowid, 'IVA', 19, 8000000, 1520000]
          );
          
          stats.documents++;
        }
      }

      console.log(`✅ Facturas insertadas: ${stats.documents}`);

      console.log('\n✅ Carga de datos de prueba completada:');
      console.log(`   📋 Terceros: ${stats.thirdParties}`);
      console.log(`   📊 Comprobantes: ${stats.journalEntries}`);
      console.log(`   📄 Facturas: ${stats.documents}`);

      return stats;

    } catch (error) {
      console.error('❌ Error al cargar datos de prueba:', error);
      throw error;
    }
  }
}

// Si se ejecuta directamente desde la línea de comandos
if (require.main === module) {
  const loader = new TestDataLoader();
  loader.loadTestData()
    .then(() => process.exit(0))
    .catch(err => {
      console.error(err);
      process.exit(1);
    });
}

module.exports = TestDataLoader;

