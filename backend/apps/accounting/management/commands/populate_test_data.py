from django.core.management.base import BaseCommand
from apps.accounting.models import ThirdParty, JournalEntry, JournalEntryLine, Account
from django.utils import timezone
from datetime import date
from decimal import Decimal

class Command(BaseCommand):
    help = 'Carga datos de prueba (Terceros y Comprobantes) similares a la versión de escritorio'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Comenzando carga de datos de prueba...'))
        
        # 1. Cargar Terceros
        self.load_third_parties()
        
        # 2. Cargar Comprobantes
        self.load_journal_entries()
        
        self.stdout.write(self.style.SUCCESS('¡Datos de prueba cargados correctamente!'))

    def load_third_parties(self):
        self.stdout.write('Cargando terceros...')
        
        third_parties_data = [
            {
                'identification_type': '31', # NIT
                'identification_number': '900123456',
                'check_digit': '3',
                'business_name': 'DISTRIBUIDORA NACIONAL S.A.S',
                'trade_name': 'DISTRINACIONAL',
                'person_type': 1, # Juridica
                'party_type': 'CLIENTE',
                'tax_regime': '48', # Responsable IVA
                'address': 'Calle 100 # 15-20',
                'city_code': '11001',
                'department_code': '11',
                'phone': '6012345678',
                'email': 'ventas@distrinacional.com',
                'country_code': 'CO',
                'postal_code': '11001',
                'ciiu_code': '0000'
            },
            {
                'identification_type': '31',
                'identification_number': '800234567',
                'check_digit': '8',
                'business_name': 'COMERCIALIZADORA DEL CARIBE LTDA',
                'trade_name': 'COMCARIBE',
                'person_type': 1,
                'party_type': 'CLIENTE',
                'tax_regime': '48',
                'address': 'Carrera 50 # 80-45',
                'city_code': '08001', # Barranquilla
                'department_code': '08',
                'phone': '6053456789',
                'email': 'info@comcaribe.com',
                'country_code': 'CO',
                'postal_code': '08001',
                'ciiu_code': '0000'
            },
            {
                'identification_type': '31',
                'identification_number': '600456789',
                'check_digit': '5',
                'business_name': 'PROVEEDORA DE INSUMOS S.A.S',
                'trade_name': 'PROINSUMOS',
                'person_type': 1,
                'party_type': 'PROVEEDOR',
                'tax_regime': '48',
                'address': 'Calle 45 # 30-15',
                'city_code': '11001',
                'department_code': '11',
                'phone': '6015678901',
                'email': 'ventas@proinsumos.com',
                'country_code': 'CO',
                'postal_code': '11001',
                'ciiu_code': '0000'
            },
            {
                'identification_type': '13', # CC
                'identification_number': '1234567890',
                'first_name': 'JUAN CARLOS',
                'surname': 'RODRIGUEZ MARTINEZ',
                'person_type': 2, # Natural
                'party_type': 'CLIENTE',
                'tax_regime': '49', # Simplificado
                'address': 'Calle 20 # 10-30',
                'city_code': '11001',
                'department_code': '11',
                'phone': '3101234567',
                'email': 'jcrodriguez@email.com',
                'country_code': 'CO',
                'postal_code': '11001',
                'ciiu_code': '0000'
            }
        ]

        count = 0
        for data in third_parties_data:
            tp, created = ThirdParty.objects.update_or_create(
                identification_number=data['identification_number'],
                defaults=data
            )
            if created:
                count += 1
        
        self.stdout.write(f'  - {count} terceros creados.')

    def load_journal_entries(self):
        self.stdout.write('Cargando comprobantes contables...')
        
        # 1. Comprobante de Apertura
        entry1_data = {
            'number': 'CE-001',
            'date': date(2026, 1, 1),
            'entry_type': 'APERTURA',
            'description': 'Comprobante de apertura año 2026',
            'status': 'POSTED',
        }
        
        # Verificar si existe para no duplicar
        if not JournalEntry.objects.filter(number=entry1_data['number']).exists():
            entry1 = JournalEntry.objects.create(**entry1_data)
            
            # Lineas
            self.create_line(entry1, '110505', 'Saldo inicial Caja General', Decimal('5000000'), Decimal('0'))
            self.create_line(entry1, '111005', 'Saldo inicial Banco Nacional', Decimal('50000000'), Decimal('0'))
            self.create_line(entry1, '310505', 'Capital inicial', Decimal('0'), Decimal('55000000'))
            
            self.stdout.write(f'  - Comprobante {entry1.number} creado.')

        # 2. Comprobante de Compra
        entry2_data = {
            'number': 'CE-002',
            'date': date(2026, 1, 5),
            'entry_type': 'DIARIO',
            'description': 'Compra de mercancía PROINSUMOS',
            'status': 'POSTED',
        }
        
        if not JournalEntry.objects.filter(number=entry2_data['number']).exists():
            entry2 = JournalEntry.objects.create(**entry2_data)
            
            # Lineas
            self.create_line(entry2, '143505', 'Compra mercancía para reventa', Decimal('10000000'), Decimal('0'))
            self.create_line(entry2, '240805', 'IVA compras 19%', Decimal('1900000'), Decimal('0'))
            # Buscar el proveedor para asignarlo
            proveedor = ThirdParty.objects.filter(identification_number='600456789').first()
            self.create_line(entry2, '220505', 'Proveedor PROINSUMOS', Decimal('0'), Decimal('11900000'), third_party=proveedor)
            
            self.stdout.write(f'  - Comprobante {entry2.number} creado.')

    def create_line(self, entry, account_code, description, debit, credit, third_party=None):
        try:
            # Buscar cuenta por código (asume que el PUC ya está cargado con load-puc)
            # Como usamos match exacto, debemos asegurarnos que '110505' exista
            # Si no existe, intentaremos buscar una aproximada o crearla dummy para el test
            account = Account.objects.filter(code=account_code).first()
            
            if not account:
                self.stdout.write(self.style.WARNING(f'    Cuenta {account_code} no encontrada. Saltando línea.'))
                return

            JournalEntryLine.objects.create(
                entry=entry,
                line_number=entry.lines.count() + 1,
                account=account,
                description=description,
                debit=debit,
                credit=credit,
                third_party=third_party
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al crear línea: {e}'))
