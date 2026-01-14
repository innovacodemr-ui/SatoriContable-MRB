from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import Invoice, SupportDocument
from apps.accounting.models import JournalEntry, JournalEntryLine, Account, AccountingDocumentType
from decimal import Decimal

@receiver(post_save, sender=Invoice)
def create_invoice_journal_entry(sender, instance, **kwargs):
    """
    Genera automáticamente el Asiento Contable cuando una Factura pasa a estado POSTED.
    TAMBIÉN inicia el proceso de firma digital para la DIAN.
    """
    if instance.status != 'POSTED':
        return

    # --- INTEGRACIÓN DIAN: Firma Electrónica ---
    if not instance.xml_file:
        try:
            from apps.invoicing.services import DianService
            from django.core.files.base import ContentFile
            from lxml import etree
            
            print(f"🔏 Iniciando Firma Digital para Factura {instance.prefix}{instance.number}...")
            service = DianService(instance.client)
            
            # 1. Generar XML
            xml_etree = service.generate_invoice_xml(instance)
            
            # 2. Firmar XML
            signed_xml = service.sign_xml(xml_etree)
            
            # 3. Guardar XML Firmado
            xml_bytes = etree.tostring(signed_xml, pretty_print=True, encoding='UTF-8', xml_declaration=True)
            filename = f"fv_{instance.prefix}{instance.number}_{timezone.now().strftime('%Y%m%d%H%M%S')}.xml"
            
            # Guardamos sin disparar señales recursivas (update_fields no dispara post_save si se usa save, pero aquí usamos instance.xml_file.save que sí guarda el modelo)
            # Para evitar recursión infinita, verificamos instance.xml_file arriba.
            instance.xml_file.save(filename, ContentFile(xml_bytes), save=False)
            instance.cufe = "DUMMY-CUFE-FIRMADO" # Idealmente calculado del XML
            instance.status = 'SENT' # Simulamos envío inmediato
            instance.save(update_fields=['xml_file', 'cufe', 'status'])
            
            print(f"✅ Factura Firmada y 'Enviada' (Simulado): {filename}")
            
        except Exception as e:
            print(f"❌ Error en Firma Digital: {str(e)}")
            # No bloqueamos el asiento contable si falla la firma (o tal vez sí deberíamos? Política de negocio)
            # Por ahora continuamos.

    # Evitar duplicados: Verificar si ya existe un asiento para esta factura
    ct = ContentType.objects.get_for_model(Invoice)
    if JournalEntry.objects.filter(client=instance.client, content_type=ct, object_id=instance.id).exists():
        return

    print(f"🔄 Generando Asiento Contable para Factura {instance.prefix}{instance.number}...")

    # 1. Definir Cuentas (Hardcoded para Prototipo - Deberían venir de configuración)
    try:
        # --- FIX: Multi-tenant Lookup ---
        acc_receivable = Account.objects.get(client=instance.client, code='130505') # Clientes Nacionales
        acc_revenue = Account.objects.get(client=instance.client, code='413505')    # Ingresos (Comercio)
        acc_tax = Account.objects.get(client=instance.client, code='240801')        # IVA Generado
    except Account.DoesNotExist as e:
        print(f"❌ Error Contable: Una o más cuentas base no fueron encontradas para el cliente {instance.client.id}. ({str(e)})")
        # Opcional: Podríamos cambiar el estado de la factura a 'ERROR'
        return

    # 2. Buscar Tipo de Documento (FV) - Específico del Tenant
    # --- FIX: Multi-tenant Lookup ---
    doc_type, _ = AccountingDocumentType.objects.get_or_create(
        client=instance.client,
        code='FV',
        defaults={'name': 'Factura de Venta'}
    )

    # 3. Crear Cabecera de Asiento
    # Incrementar consecutivo de forma segura
    doc_type.current_number = doc_type.current_number + 1
    doc_type.save(update_fields=['current_number'])

    # --- FIX: Multi-tenant Creation ---
    journal_entry = JournalEntry.objects.create(
        client=instance.client,
        document_type=doc_type,
        number=f"{doc_type.code}-{doc_type.current_number}",
        entry_type='DIARIO',
        date=instance.issue_date,
        description=f"Venta Factura {instance.prefix}{instance.number} a {instance.customer.business_name or instance.customer}",
        content_type=ct,
        object_id=instance.id,
        status='POSTED',
        created_by=None # Idealmente, aquí iría el usuario que posteó la factura
    )

    # 4. Crear Líneas (Debito y Credito)
    
    # A. Débito a Cuentas por Cobrar (Valor Total de la Factura)
    JournalEntryLine.objects.create(
        client=instance.client,
        entry=journal_entry,
        line_number=1,
        account=acc_receivable,
        third_party=instance.customer,
        description=f"CxC Factura {instance.prefix}{instance.number}",
        debit=instance.total,
        credit=Decimal('0.00')
    )

    line_number_counter = 2
    total_tax_from_lines = Decimal('0.00')

    # B. Créditos a Ingresos y Impuestos (por cada línea de la factura)
    for line in instance.lines.all():
        # Lógica de validación de Centro de Costo
        cost_center_to_assign = line.cost_center
        if acc_revenue.requires_cost_center and not cost_center_to_assign:
            print(f"⚠️ Alerta: La cuenta de ingreso {acc_revenue.code} requiere Centro de Costo, pero no se proveyó en la línea de factura '{line.description}'. El asiento podría ser inválido.")
            # En un escenario más estricto, podríamos abortar la operación aquí.
            # Por ahora, se registrará sin C.C. y se marcará la alerta.

        # Crédito al ingreso
        JournalEntryLine.objects.create(
            client=instance.client,
            entry=journal_entry,
            line_number=line_number_counter,
            account=acc_revenue, # Simplificado: todas las líneas van a la misma cuenta de ingreso
            third_party=instance.customer,
            cost_center=cost_center_to_assign, # Asignación del Centro de Costo
            description=line.description,
            debit=Decimal('0.00'),
            credit=line.subtotal
        )
        line_number_counter += 1

        if line.tax_amount > 0:
            total_tax_from_lines += line.tax_amount

    # C. Crédito a la cuenta de Impuestos (IVA) - Sumarizado
    if total_tax_from_lines > 0:
        JournalEntryLine.objects.create(
            client=instance.client,
            entry=journal_entry,
            line_number=line_number_counter,
            account=acc_tax,
            third_party=instance.customer, # Simplificado
            description=f"IVA Generado Factura {instance.prefix}{instance.number}",
            debit=Decimal('0.00'),
            credit=total_tax_from_lines
        )

    # Validar que el asiento haya quedado balanceado
    journal_entry.save() # Llama al clean() y puede lanzar ValidationError

    print(f"✅ Asiento Contable Multi-Tenant Creado: {journal_entry.number}")


@receiver(post_save, sender=SupportDocument)
def create_support_document_journal_entry(sender, instance, **kwargs):
    """
    Genera automáticamente el Asiento Contable para un Documento Soporte
    cuando pasa a estado ACEPTADO.
    """
    if instance.dian_status != 'ACCEPTED':
        return

    ct = ContentType.objects.get_for_model(SupportDocument)
    if JournalEntry.objects.filter(client=instance.client, content_type=ct, object_id=instance.id).exists():
        return

    print(f"🔄 Generando Asiento Contable para Documento Soporte {instance.prefix}{instance.consecutive}...")

    try:
        acc_payable = Account.objects.get(client=instance.client, code='220505') # Proveedores Nacionales
        acc_expense = Account.objects.get(client=instance.client, code='513595') # Gastos (Otros)
        acc_tax_credit = Account.objects.get(client=instance.client, code='240810') # IVA Descontable
    except Account.DoesNotExist as e:
        print(f"❌ Error Contable: Cuentas base para compras no encontradas para el cliente {instance.client.id}. ({str(e)})")
        return

    doc_type, _ = AccountingDocumentType.objects.get_or_create(
        client=instance.client,
        code='DS',
        defaults={'name': 'Documento Soporte'}
    )

    doc_type.current_number += 1
    doc_type.save(update_fields=['current_number'])

    journal_entry = JournalEntry.objects.create(
        client=instance.client,
        document_type=doc_type,
        number=f"{doc_type.code}-{doc_type.current_number}",
        entry_type='DIARIO',
        date=instance.issue_date,
        description=f"Compra s/g DS {instance.prefix}{instance.consecutive} a {instance.supplier.name}",
        content_type=ct,
        object_id=instance.id,
        status='POSTED'
    )

    # CRÉDITO a Cuentas por Pagar (Total del Documento)
    JournalEntryLine.objects.create(
        client=instance.client,
        entry=journal_entry,
        line_number=1,
        account=acc_payable,
        third_party=instance.supplier,
        description=f"CxP DS {instance.prefix}{instance.consecutive}",
        debit=Decimal('0.00'),
        credit=instance.total
    )

    line_counter = 2
    total_tax_from_lines = Decimal('0.00')

    # DÉBITOS a Gastos/Costos (por cada línea del documento)
    for line in instance.items.all():
        cost_center_to_assign = line.cost_center
        if acc_expense.requires_cost_center and not cost_center_to_assign:
            print(f"⚠️ Alerta: La cuenta de gasto {acc_expense.code} requiere C.C., pero no se proveyó en la línea de DS '{line.description}'.")

        JournalEntryLine.objects.create(
            client=instance.client,
            entry=journal_entry,
            line_number=line_counter,
            account=acc_expense, # Simplificado: todo va a la misma cuenta de gasto
            third_party=instance.supplier,
            cost_center=cost_center_to_assign,
            description=line.description,
            debit=line.total_line, # total_line en SupportDocumentDetail es el subtotal de esa línea
            credit=Decimal('0.00')
        )
        line_counter += 1
        
        # Calcular impuesto por línea
        tax_on_line = line.total_line * (line.tax_rate / Decimal(100))
        total_tax_from_lines += tax_on_line

    # DÉBITO a Impuestos por Pagar (IVA Descontable)
    if total_tax_from_lines > 0:
        JournalEntryLine.objects.create(
            client=instance.client,
            entry=journal_entry,
            line_number=line_counter,
            account=acc_tax_credit,
            third_party=instance.supplier,
            description=f"IVA Descontable DS {instance.prefix}{instance.consecutive}",
            debit=total_tax_from_lines,
            credit=Decimal('0.00')
        )
    
    journal_entry.save()

    print(f"✅ Asiento Contable de Compra Creado: {journal_entry.number}")
