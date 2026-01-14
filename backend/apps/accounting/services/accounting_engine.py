from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from apps.accounting.models import JournalEntry, JournalEntryLine, AccountingTemplate

class AccountingEngine:
    @staticmethod
    @transaction.atomic
    def generate_entry(document, template, third_party):
        """
        Genera un asiento contable automático basado en un documento y una plantilla.
        """
        # 1. Obtener valores base del documento
        # Se asume que el documento tiene estas propiedades o atributos
        # Si es un diccionario, usar .get(), si es objeto usar getattr
        if isinstance(document, dict):
            subtotal = Decimal(str(document.get('subtotal_amount', 0)))
            tax = Decimal(str(document.get('tax_amount', 0)))
            total = Decimal(str(document.get('total_amount', 0)))
            doc_number = document.get('invoice_number', 'S/N')
            doc_date = document.get('issue_date', timezone.now().date())
        else:
            subtotal = getattr(document, 'subtotal_amount', Decimal('0'))
            tax = getattr(document, 'tax_amount', Decimal('0'))
            total = getattr(document, 'total_amount', Decimal('0'))
            doc_number = getattr(document, 'invoice_number', 'S/N')
            doc_date = getattr(document, 'issue_date', timezone.now().date())

        # 2. Crear cabecera del Asiento
        # Usamos GenericForeignKey para vincular al documento
        content_type = ContentType.objects.get_for_model(document)
        
        entry = JournalEntry.objects.create(
            document_type=template.document_type,
            number=f"AUTO-{doc_number}", # Se debería usar una secuencia real
            entry_type='DIARIO', # O lo que defina el doctype
            date=doc_date,
            description=f"Asiento Automático - {template.name}",
            content_type=content_type,
            object_id=document.pk,
            status='DRAFT'
        )

        # 3. Procesar líneas
        lines_to_create = []
        total_debits = Decimal('0')
        total_credits = Decimal('0')
        plug_line_config = None
        
        # Variables para descripción dinámica
        desc_context = {
            'numero': doc_number,
            'tercero': third_party.get_full_name() if third_party else 'Sin Tercero',
            'fecha': str(doc_date)
        }

        for line_config in template.lines.all():
            amount = Decimal('0')
            description = line_config.description_template.format(**desc_context)

            if line_config.calculation_method == 'PLUG':
                plug_line_config = line_config
                continue # Procesar al final
            
            elif line_config.calculation_method == 'FIXED_VALUE':
                amount = line_config.value
            
            elif line_config.calculation_method == 'PERCENTAGE_OF_SUBTOTAL':
                amount = subtotal * (line_config.value / Decimal('100.00'))
            
            elif line_config.calculation_method == 'PERCENTAGE_OF_TOTAL':
                amount = total * (line_config.value / Decimal('100.00'))
            
            elif line_config.calculation_method == 'PERCENTAGE_OF_TAX':
                amount = tax * (line_config.value / Decimal('100.00'))
            
            # Redondear a 2 decimales
            amount = amount.quantize(Decimal('0.01'))

            # Acumular
            debit = amount if line_config.nature == 'DEBITO' else Decimal('0')
            credit = amount if line_config.nature == 'CREDITO' else Decimal('0')
            
            total_debits += debit
            total_credits += credit

            lines_to_create.append(JournalEntryLine(
                entry=entry,
                line_number=0, # Se asignará al final
                account=line_config.account,
                third_party=third_party,
                description=description,
                debit=debit,
                credit=credit
            ))

        # 4. Calcular PLUG si existe
        if plug_line_config:
            diff = total_debits - total_credits
            
            # Si hay más débitos, necesitamos créditos para cuadrar (diff > 0) -> Crédito
            # Si hay más créditos, necesitamos débitos para cuadrar (diff < 0) -> Débito
            
            description = plug_line_config.description_template.format(**desc_context)
            
            plug_debit = Decimal('0')
            plug_credit = Decimal('0')

            # La naturaleza configurada en el PLUG es la "esperada", pero matemáticamente debe cuadrar
            # Opción 1: Respetar la naturaleza configurada y poner la diferencia ahí (si coincide el signo)
            # Opción 2: Usar la naturaleza necesaria para cuadrar.
            # Implementamos Opción 2 (Cuadre matemático forzoso) pero intentamos respetar config si es posible.
            
            # Cálculo del valor necesario para balancear
            required_amount = abs(diff)
            
            if diff > 0:
                # Debitos > Creditos => Faltan Creditos
                plug_credit = required_amount
                plug_debit = Decimal('0')
            else:
                # Creditos > Debitos => Faltan Debitos
                plug_debit = required_amount
                plug_credit = Decimal('0')
            
            lines_to_create.append(JournalEntryLine(
                entry=entry,
                line_number=0,
                account=plug_line_config.account,
                third_party=third_party,
                description=description,
                debit=plug_debit,
                credit=plug_credit
            ))

        # 5. Guardar líneas con número consecutivo
        for i, line in enumerate(lines_to_create, 1):
            line.line_number = i
            line.save()

        # 6. Validar (si quisiéramos postear)
        # if entry.is_balanced():
        #     entry.status = 'POSTED'
        #     entry.save()

        return entry
