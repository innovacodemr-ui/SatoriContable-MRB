"""
Management command to load test data (third parties, journal entries, electronic documents)
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from apps.accounting.models import Account, ThirdParty, JournalEntry, JournalEntryLine
from apps.dian.models import ElectronicDocument, ElectronicDocumentLine, ElectronicDocumentTax, TaxType


class Command(BaseCommand):
    help = 'Carga datos de prueba (terceros, comprobantes, facturas)'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Cargando datos de prueba...\n')
        
        # Cargar terceros
        terceros_count = self.load_terceros()
        self.stdout.write(self.style.SUCCESS(f'✅ Terceros insertados: {terceros_count}'))
        
        # Cargar comprobantes
        comprobantes_count = self.load_comprobantes()
        self.stdout.write(self.style.SUCCESS(f'✅ Comprobantes insertados: {comprobantes_count}'))
        
        # Cargar facturas electrónicas
        facturas_count = self.load_facturas()
        self.stdout.write(self.style.SUCCESS(f'✅ Facturas insertadas: {facturas_count}\n'))
        
        self.stdout.write(self.style.SUCCESS('✅ Carga de datos de prueba completada'))

    def load_terceros(self):
        """Crear 8 terceros de prueba con campos DIAN"""
        terceros_data = [
            {
                'party_type': 'PROVEEDOR',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '900123456',
                'business_name': 'DISTRIBUIDORA NACIONAL S.A.',
                'trade_name': 'DISTRIBUIDORA NACIONAL',
                'email': 'ventas@distribuidoranacional.com',
                'phone': '3001234567',
                'address': 'Calle 100 # 15-20',
                'department_code': '11',
                'city_code': '11001',
                'postal_code': '110111',
                'tax_regime': '48',
                'fiscal_responsibilities': ['O-13', 'O-15'],
                'ciiu_code': '4631'
            },
            {
                'party_type': 'PROVEEDOR',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '800234567',
                'business_name': 'COMERCIALIZADORA DEL CARIBE LTDA',
                'trade_name': 'COMCARIBE',
                'email': 'info@comcaribe.com',
                'phone': '3109876543',
                'address': 'Carrera 45 # 76-123',
                'department_code': '08',
                'city_code': '08001',
                'postal_code': '080001',
                'tax_regime': '48',
                'fiscal_responsibilities': [],
                'ciiu_code': '4632'
            },
            {
                'party_type': 'CLIENTE',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '700345678',
                'business_name': 'INVERSIONES ANTIOQUEÑAS S.A.S.',
                'trade_name': 'INVERANTIOQUIA',
                'email': 'contacto@inverantioquia.com',
                'phone': '3145678901',
                'address': 'Avenida El Poblado # 10-50',
                'department_code': '05',
                'city_code': '05001',
                'postal_code': '050001',
                'tax_regime': '48',
                'fiscal_responsibilities': ['O-23'],
                'ciiu_code': '6820'
            },
            {
                'party_type': 'PROVEEDOR',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '600456789',
                'business_name': 'PRODUCTOS E INSUMOS DEL VALLE',
                'trade_name': 'PROINSUMOS',
                'email': 'ventas@proinsumos.com',
                'phone': '3187654321',
                'address': 'Calle 5 # 38-25',
                'department_code': '76',
                'city_code': '76001',
                'postal_code': '760001',
                'tax_regime': '48',
                'fiscal_responsibilities': [],
                'ciiu_code': '4669'
            },
            {
                'party_type': 'CLIENTE',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '500567890',
                'business_name': 'SUMINISTROS INDUSTRIALES LTDA',
                'trade_name': 'SUMIND',
                'email': 'compras@sumind.com',
                'phone': '3192345678',
                'address': 'Carrera 30 # 45-67',
                'department_code': '68',
                'city_code': '68001',
                'postal_code': '680001',
                'tax_regime': '48',
                'fiscal_responsibilities': [],
                'ciiu_code': '4663'
            },
            {
                'party_type': 'EMPLEADO',
                'person_type': 2,  # Natural
                'identification_type': '13',  # Cédula
                'identification_number': '1234567890',
                'first_name': 'JUAN CARLOS',
                'surname': 'RODRIGUEZ',
                'second_surname': 'MARTINEZ',
                'email': 'jrodriguez@empresa.com',
                'phone': '3123456789',
                'address': 'Calle 25 # 10-30',
                'department_code': '11',
                'city_code': '11001',
                'postal_code': '110111',
                'tax_regime': '49',
                'fiscal_responsibilities': ['R-99-PN'],
                'ciiu_code': ''
            },
            {
                'party_type': 'EMPLEADO',
                'person_type': 2,  # Natural
                'identification_type': '13',  # Cédula
                'identification_number': '9876543210',
                'first_name': 'MARIA FERNANDA',
                'surname': 'GOMEZ',
                'second_surname': 'LOPEZ',
                'email': 'mgomez@empresa.com',
                'phone': '3134567890',
                'address': 'Carrera 15 # 80-45',
                'department_code': '11',
                'city_code': '11001',
                'postal_code': '110111',
                'tax_regime': '49',
                'fiscal_responsibilities': ['R-99-PN'],
                'ciiu_code': ''
            },
            {
                'party_type': 'PROVEEDOR',
                'person_type': 1,  # Jurídica
                'identification_type': '31',  # NIT
                'identification_number': '400678901',
                'business_name': 'SERVICIOS CONTABLES Y AUDITORIA S.A.S.',
                'trade_name': 'SERCONTAUD',
                'email': 'contacto@sercontaud.com',
                'phone': '3156789012',
                'address': 'Calle 72 # 10-50 Of. 301',
                'department_code': '11',
                'city_code': '11001',
                'postal_code': '110111',
                'tax_regime': '48',
                'fiscal_responsibilities': ['O-15'],
                'ciiu_code': '6920'
            }
        ]
        
        count = 0
        for data in terceros_data:
            ThirdParty.objects.get_or_create(
                identification_number=data['identification_number'],
                defaults=data
            )
            count += 1
        
        return count

    def get_account(self, code):
        """Helper para obtener cuenta por código"""
        return Account.objects.filter(code=code).first()

    def load_comprobantes(self):
        """Crear 3 comprobantes de prueba"""
        count = 0
        
        # Comprobante 1: Apertura
        apertura, created = JournalEntry.objects.get_or_create(
            number='CE-001',
            defaults={
                'date': timezone.now().date() - timedelta(days=90),
                'description': 'Comprobante de Apertura - Capital Inicial',
                'entry_type': 'APERTURA',
                'status': 'POSTED'
            }
        )
        
        if created:
            JournalEntryLine.objects.create(
                entry=apertura,
                line_number=1,
                account=self.get_account('110505'),  # Caja General
                description='Aporte inicial en efectivo',
                debit=15000000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=apertura,
                line_number=2,
                account=self.get_account('111005'),  # Bancos
                description='Apertura cuenta bancaria',
                debit=30000000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=apertura,
                line_number=3,
                account=self.get_account('143505'),  # Inventarios
                description='Inventario inicial mercancías',
                debit=10000000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=apertura,
                line_number=4,
                account=self.get_account('310505'),  # Capital Social
                description='Aporte de capital socios',
                debit=0,
                credit=55000000
            )
        count += 1
        
        # Comprobante 2: Compra (uso DIARIO ya que COMPRA no está en las opciones)
        compra, created = JournalEntry.objects.get_or_create(
            number='CE-002',
            defaults={
                'date': timezone.now().date() - timedelta(days=60),
                'description': 'Compra de Mercancía a Crédito',
                'entry_type': 'DIARIO',
                'status': 'POSTED'
            }
        )
        
        if created:
            proveedor = ThirdParty.objects.filter(identification_number='900123456').first()
            
            JournalEntryLine.objects.create(
                entry=compra,
                line_number=1,
                account=self.get_account('143505'),  # Inventarios
                third_party=proveedor,
                description='Compra mercancía DISTRIBUIDORA NACIONAL',
                debit=10000000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=compra,
                line_number=2,
                account=self.get_account('240805'),  # IVA por Pagar
                third_party=proveedor,
                description='IVA compras 19%',
                debit=1900000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=compra,
                line_number=3,
                account=self.get_account('220505'),  # Proveedores Nacionales
                third_party=proveedor,
                description='Compra a crédito DISTRIBUIDORA NACIONAL',
                debit=0,
                credit=11900000
            )
        count += 1
        
        # Comprobante 3: Gastos (uso DIARIO ya que EGRESO no está en las opciones)
        gastos, created = JournalEntry.objects.get_or_create(
            number='CE-003',
            defaults={
                'date': timezone.now().date() - timedelta(days=30),
                'description': 'Pago de Gastos Operacionales',
                'entry_type': 'DIARIO',
                'status': 'POSTED'
            }
        )
        
        if created:
            JournalEntryLine.objects.create(
                entry=gastos,
                line_number=1,
                account=self.get_account('513505'),  # Energía Eléctrica
                description='Energía eléctrica',
                debit=500000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=gastos,
                line_number=2,
                account=self.get_account('512005'),  # Arrendamientos
                description='Arriendo local comercial',
                debit=2000000,
                credit=0
            )
            
            JournalEntryLine.objects.create(
                entry=gastos,
                line_number=3,
                account=self.get_account('110505'),  # Caja General
                description='Pago gastos en efectivo',
                debit=0,
                credit=2500000
            )
        count += 1
        
        return count

    def load_facturas(self):
        """Crear 2 facturas electrónicas de prueba"""
        count = 0
        
        # Obtener o crear tipo de impuesto IVA
        iva_tax, _ = TaxType.objects.get_or_create(
            code='01',
            defaults={
                'name': 'IVA',
                'description': 'Impuesto al Valor Agregado',
                'category': 'IVA',
                'default_rate': Decimal('19.00'),
                'is_active': True
            }
        )
        
        # Factura 1: Venta de contado
        cliente1 = ThirdParty.objects.filter(identification_number='700345678').first()
        
        factura1, created = ElectronicDocument.objects.get_or_create(
            full_number='SEFE-00001',
            defaults={
                'document_type': 'INVOICE',
                'prefix': 'SEFE',
                'number': '1',
                'issue_date': timezone.now().date() - timedelta(days=15),
                'due_date': timezone.now().date() - timedelta(days=15),
                'customer': cliente1,
                'payment_method': 'CASH',
                'currency': 'COP',
                'cufe': 'CUFE-SEFE-00001-' + timezone.now().strftime('%Y%m%d%H%M%S'),
                'status': 'ACCEPTED',
                'subtotal': Decimal('5000000.00'),
                'discount_total': Decimal('0.00'),
                'tax_total': Decimal('950000.00'),
                'total': Decimal('5950000.00'),
                'notes': 'Venta de contado'
            }
        )
        
        if created:
            ElectronicDocumentLine.objects.create(
                document=factura1,
                line_number=1,
                product_code='PROD-001',
                product_name='Producto A - Alta Calidad',
                description='Producto A de alta calidad',
                quantity=Decimal('50.00'),
                unit_of_measure='UND',
                unit_price=Decimal('80000.00'),
                subtotal=Decimal('4000000.00'),
                discount_amount=Decimal('0.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('760000.00'),
                total=Decimal('4760000.00')
            )
            
            ElectronicDocumentLine.objects.create(
                document=factura1,
                line_number=2,
                product_code='PROD-002',
                product_name='Producto B - Estándar',
                description='Producto B estándar',
                quantity=Decimal('20.00'),
                unit_of_measure='UND',
                unit_price=Decimal('50000.00'),
                subtotal=Decimal('1000000.00'),
                discount_amount=Decimal('0.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('190000.00'),
                total=Decimal('1190000.00')
            )
            
            ElectronicDocumentTax.objects.create(
                document=factura1,
                tax_type=iva_tax,
                taxable_amount=Decimal('5000000.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('950000.00')
            )
        count += 1
        
        # Factura 2: Venta a crédito
        cliente2 = ThirdParty.objects.filter(identification_number='500567890').first()
        
        factura2, created = ElectronicDocument.objects.get_or_create(
            full_number='SEFE-00002',
            defaults={
                'document_type': 'INVOICE',
                'prefix': 'SEFE',
                'number': '2',
                'issue_date': timezone.now().date() - timedelta(days=7),
                'due_date': timezone.now().date() + timedelta(days=23),
                'customer': cliente2,
                'payment_method': 'CREDIT',
                'currency': 'COP',
                'cufe': 'CUFE-SEFE-00002-' + timezone.now().strftime('%Y%m%d%H%M%S'),
                'status': 'ACCEPTED',
                'subtotal': Decimal('8000000.00'),
                'discount_total': Decimal('0.00'),
                'tax_total': Decimal('1520000.00'),
                'total': Decimal('9520000.00'),
                'notes': 'Venta a crédito 30 días'
            }
        )
        
        if created:
            ElectronicDocumentLine.objects.create(
                document=factura2,
                line_number=1,
                product_code='PROD-003',
                product_name='Producto C - Premium',
                description='Producto C premium',
                quantity=Decimal('40.00'),
                unit_of_measure='UND',
                unit_price=Decimal('150000.00'),
                subtotal=Decimal('6000000.00'),
                discount_amount=Decimal('0.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('1140000.00'),
                total=Decimal('7140000.00')
            )
            
            ElectronicDocumentLine.objects.create(
                document=factura2,
                line_number=2,
                product_code='PROD-001',
                product_name='Producto A - Alta Calidad',
                description='Producto A de alta calidad',
                quantity=Decimal('25.00'),
                unit_of_measure='UND',
                unit_price=Decimal('80000.00'),
                subtotal=Decimal('2000000.00'),
                discount_amount=Decimal('0.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('380000.00'),
                total=Decimal('2380000.00')
            )
            
            ElectronicDocumentTax.objects.create(
                document=factura2,
                tax_type=iva_tax,
                taxable_amount=Decimal('8000000.00'),
                tax_rate=Decimal('19.00'),
                tax_amount=Decimal('1520000.00')
            )
        count += 1
        
        return count
