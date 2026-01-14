from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from faker import Faker
import random
from decimal import Decimal
from datetime import timedelta

# Model Imports
from apps.tenants.models import Client as Company
from apps.invoicing.models import (
    ElectronicBillingConfig, 
    DianResolution, 
    Item, 
    Invoice, 
    InvoiceLine
)
from apps.accounting.models import ThirdParty
from apps.electronic_events.models import ReceivedInvoice
from apps.treasury.models import PaymentOut, PaymentOutDetail, BankAccount, Account

class Command(BaseCommand):
    help = 'Poblar base de datos con datos de prueba para una Compañía (Tenant) específica'

    def add_arguments(self, parser):
        parser.add_argument('--nit', type=str, required=True, help='NIT de la compañía para la cual crear datos')

    def handle(self, *args, **options):
        nit = options['nit']
        self.stdout.write(self.style.WARNING(f'Iniciando Seeding para empresa con NIT: {nit}...'))
        
        try:
            company = Company.objects.get(nit=nit)
            self.stdout.write(self.style.SUCCESS(f'Empresa encontrada: {company.business_name}'))
        except Company.DoesNotExist:
            raise CommandError(f'No existe empresa con NIT {nit}')

        # --- CONTEXTO DE TENANT ---
        # Activamos el contexto para este comando.
        from apps.tenants.utils import set_current_client_id
        set_current_client_id(company.id)
        # --------------------------

        try:
            fake = Faker('es_CO')
            
            # 1. Configuración Fiscal (Fake)
            self.create_fiscal_config(company)
            
            # 2. Resoluciones
            resolution = self.create_resolutions(company)
            
            # 3. Terceros
            clients = self.create_third_parties(company, fake, 'CLIENTE', 10)
            suppliers = self.create_third_parties(company, fake, 'PROVEEDOR', 10)
            employees = self.create_third_parties(company, fake, 'EMPLEADO', 10) # Used for payroll later maybe
            
            # 4. Inventario
            items = self.create_inventory(company, fake)
            
            # 5. Ventas (Invoices)
            self.create_sales(company, fake, resolution, clients, items)
            
            # 6. Compras (Received Invoices - "SupplierInvoice")
            supplier_invoices = self.create_purchases(company, fake, suppliers)
            
            # 7. Tesorería (Pagos a Proveedores)
            # Note: "Recibos de Caja" (Customer Payments) model was not found in quick inspection, 
            # implementing PaymentOut (Payments to Suppliers) instead as per available models.
            self.create_treasury_out(company, fake, supplier_invoices)

            self.stdout.write(self.style.SUCCESS('--------------------------------------------------'))
            self.stdout.write(self.style.SUCCESS('✅ SEEDING COMPLETADO CON ÉXITO.'))
            self.stdout.write(self.style.SUCCESS('--------------------------------------------------'))
        
        finally:
            # --- LIMPIEZA DE CONTEXTO ---
            set_current_client_id(None)
            self.stdout.write(self.style.WARNING('Contexto de tenant limpiado.'))

    def create_fiscal_config(self, company):
        # NOTA: Este modelo parece tener 'company' en lugar de 'client'. Se respeta.
        if not hasattr(company, 'electronic_billing_config'):
            ElectronicBillingConfig.objects.create(
                company=company,
                environment='PRUEBAS',
                software_id='fc8eac42-2eba-4d5e-9637-846c98', # Fake but valid format
                software_pin='12345',
                certificate_password='Password123!',
                invoice_test_set_id='85f4e5a2-3f81-4b13-92f7'
            )
            self.stdout.write(self.style.SUCCESS(' > Configuración Fiscal Creada'))
        else:
            self.stdout.write(' > Configuración Fiscal ya existía')

    def create_resolutions(self, company):
        # NOTA: Este modelo parece tener 'company' en lugar de 'client'. Se respeta.
        res, created = DianResolution.objects.get_or_create(
            company=company,
            document_type='INVOICE',
            defaults={
                'prefix': 'SETP',
                'resolution_number': '18760000001',
                'date_from': timezone.now().date(),
                'date_to': timezone.now().date() + timedelta(days=365),
                'number_from': 1,
                'number_to': 5000,
                'current_number': 0,
                'technical_key': 'fc8eac422eba4d5e9637846c98',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f' > Resolución {res.prefix} creada'))
        return res

    def create_third_parties(self, company, fake, party_type, count):
        created = []
        for _ in range(count):
            # Identification logic to avoid duplicates
            ident = fake.random_number(digits=9)
            
            # Simple check to avoid crashing on unique constraint
            # TenantAwareManager se encarga de filtrar por el company.id activo en el contexto
            if ThirdParty.objects.filter(identification_number=ident).exists():
                ident = fake.random_number(digits=10)

            # Person Type map
            person_type = 1 if party_type in ['CLIENTE', 'PROVEEDOR'] else 2 # 1 Juridica, 2 Natural for Empleado
            name = fake.company() if person_type == 1 else fake.name()

            tp = ThirdParty.objects.create(
                client=company,  # <-- CAMBIO CLAVE: Se asigna el tenant
                party_type=party_type,
                person_type=person_type,
                identification_type='31' if person_type == 1 else '13',
                identification_number=str(ident),
                check_digit=str(fake.random_int(0, 9)),
                first_name=fake.first_name() if person_type == 2 else '',
                surname=fake.last_name() if person_type == 2 else '',
                business_name=name if person_type == 1 else '',
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address(),
                city_code='76001', # Cali
                is_active=True
            )
            created.append(tp)
        self.stdout.write(self.style.SUCCESS(f' > {count} {party_type}s creados'))
        return created

    def create_inventory(self, company, fake):
        items = []
        for i in range(20):
            code = f'ITEM-{fake.unique.random_number(digits=5)}'
            price = Decimal(random.randint(10000, 500000))
            
            item = Item.objects.create(
                client=company,  # <-- CAMBIO CLAVE: Se asigna el tenant
                code=code,
                description=fake.sentence(nb_words=3).replace('.', ''),
                unit_price=price,
                type='SERVICIO', # Simpler for now
                tax_type='IVA_19',
                is_active=True
            )
            items.append(item)
        self.stdout.write(self.style.SUCCESS(f' > 20 Items creados'))
        return items

    def create_sales(self, company, fake, resolution, clients, items):
        count = 0
        for _ in range(15):
            customer = random.choice(clients)
            
            # Simulate invoice numbering logic (usually handled by view/signal, but here manual for speed)
            resolution.current_number += 1
            resolution.save()
            number = resolution.current_number
            
            invoice = Invoice.objects.create(
                resolution=resolution,
                customer=customer,
                prefix=resolution.prefix,
                number=number,
                issue_date=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                payment_due_date=timezone.now().date() + timedelta(days=30),
                payment_term='30_DIAS',
                status='POSTED'
            )

            # Lines
            subtotal = Decimal(0)
            tax_total = Decimal(0)
            
            for _ in range(random.randint(1, 5)):
                item = random.choice(items)
                qty = Decimal(random.randint(1, 10))
                
                line_subtotal = qty * item.unit_price
                line_tax = line_subtotal * Decimal('0.19') # Assuming 19%
                
                InvoiceLine.objects.create(
                    invoice=invoice,
                    item=item,
                    description=item.description,
                    quantity=qty,
                    unit_price=item.unit_price,
                    tax_rate=19.00,
                    subtotal=line_subtotal,
                    tax_amount=line_tax,
                    total=line_subtotal + line_tax
                )
                
                subtotal += line_subtotal
                tax_total += line_tax
            
            invoice.subtotal = subtotal
            invoice.tax_total = tax_total
            invoice.total = subtotal + tax_total
            invoice.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f' > {count} Facturas de Venta creadas'))

    def create_purchases(self, company, fake, suppliers):
        created_invoices = []
        for i in range(10):
            supplier = random.choice(suppliers)
            amount = Decimal(random.randint(50000, 1000000))
            
            ri = ReceivedInvoice.objects.create(
                client=company,
                issuer_nit=supplier.identification_number,
                issuer_name=supplier.business_name or f"{supplier.first_name} {supplier.last_name}",
                invoice_number=f'XE-{fake.random_number(digits=6)}',
                cufe=fake.sha256(),
                issue_date=timezone.now().date() - timedelta(days=random.randint(1, 60)),
                subtotal_amount=amount,
                tax_amount=amount * Decimal('0.19'),
                total_amount=amount * Decimal('1.19'),
                # Fakes for file fields
                xml_file='seed/fake.xml', 
                pdf_file='seed/fake.pdf'
            )
            created_invoices.append(ri)
        
        self.stdout.write(self.style.SUCCESS(f' > {len(created_invoices)} Facturas Recibidas (Compras) creadas'))
        return created_invoices

    def create_treasury_out(self, company, fake, supplier_invoices):
        # Ensure at least one bank account exists
        try:
            # Create a minimal AccountClass and AccountGroup just to satisfy FKs if they don't exist
            from apps.accounting.models import AccountClass, AccountGroup
            
            # NOTA: Se asume que el Plan de Cuentas (PUC) es por tenant.
            cls, _ = AccountClass.objects.get_or_create(client=company, code='1', defaults={'name': 'ACTIVO', 'nature': 'DEBITO'})
            grp, _ = AccountGroup.objects.get_or_create(client=company, code='11', defaults={'name': 'DISPONIBLE', 'account_class': cls})
            
            gl_account, _ = Account.objects.get_or_create(
                client=company,
                code='111005',
                defaults={
                    'name': 'Bancos Nacionales', 
                    'account_group': grp,
                    'nature': 'DEBITO'
                }
            )

            bank_account, _ = BankAccount.objects.get_or_create(
                client=company,
                account_number='987654321',
                defaults={
                    'name': 'Cuenta Demo',
                    'bank_name': 'BANCOLOMBIA',
                    'gl_account': gl_account
                }
            )

            count = 0
            for i in range(5):
                # Pay a random invoice
                inv = random.choice(supplier_invoices)
                amount_to_pay = inv.total_amount / 2 # Partial payment

                # Find the supplier ThirdParty object
                try:
                    supplier = ThirdParty.objects.get(identification_number=inv.issuer_nit)
                except ThirdParty.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f' > No se encontró el tercero con NIT {inv.issuer_nit} para crear el pago.'))
                    continue

                payment = PaymentOut.objects.create(
                    client=company,
                    payment_date=timezone.now().date(),
                    third_party=supplier, # <-- CAMBIO CLAVE: Usar el objeto, no el string.
                    bank_account=bank_account,
                    total_amount=amount_to_pay,
                    status='POSTED'
                )
                
                PaymentOutDetail.objects.create(
                    payment_out=payment,
                    invoice=inv,
                    amount_paid=amount_to_pay
                )
                count += 1
            
            self.stdout.write(self.style.SUCCESS(f' > {count} Pagos a Proveedores creados'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f' > Error creando tesorería: {e}'))
