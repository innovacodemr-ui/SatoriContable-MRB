import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import ReceivedInvoice
from apps.accounting.models import AccountingTemplate, JournalEntry
from apps.accounting.services.accounting_engine import AccountingEngine
from apps.support_docs.models import Supplier

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ReceivedInvoice)
def auto_generate_accounting_entry(sender, instance, created, **kwargs):
    """
    Señal que se dispara al recibir una nueva factura electrónica.
    Busca una plantilla contable y ejecuta el AccountingEngine.
    """
    if not created:
        return

    logger.info(f"⚡ Iniciando causación automática para Factura {instance.invoice_number}")

    # 1. Buscar el Tercero (Proveedor)
    # El email_service ya debió haberlo creado, pero validamos.
    supplier = Supplier.objects.filter(identification_number=instance.issuer_nit).first()
    
    if not supplier:
        logger.warning(f"⚠️ No se encontró proveedor con NIT {instance.issuer_nit} para la factura {instance.invoice_number}. Causación abortada.")
        return

    # 2. Buscar Plantilla Contable
    # Estrategia: Buscar una plantilla marcada como activa que coincida con el contexto.
    # Por ahora, buscamos una genérica 'Recepción Factura' o la primera disponible para Facturas de Compra.
    # idealmente, esto podría configurarse en settings o en el modelo del proveedor.
    
    template = AccountingTemplate.objects.filter(
        active=True, 
        name__icontains="Recepción"
    ).first()

    if not template:
        # Fallback: Intentar buscar cualquiera activa si no hay específica
        template = AccountingTemplate.objects.filter(active=True).first()
    
    if not template:
        logger.error("❌ No hay Plantillas Contables activas configuradas. No se puede causar automáticamente.")
        return

    try:
        # 3. Validar si ya existe asiento (Idempotencia)
        content_type = ContentType.objects.get_for_model(instance)
        if JournalEntry.objects.filter(content_type=content_type, object_id=instance.pk).exists():
            logger.info(f"ℹ️ La factura {instance.invoice_number} ya tiene asiento contable.")
            return

        # 4. Ejecutar Motor Contable
        entry = AccountingEngine.generate_entry(
            document=instance,
            template=template,
            third_party=supplier
        )
        
        logger.info(f"✅ Asiento Contable {entry.number} generado exitosamente para Factura {instance.invoice_number}")

    except Exception as e:
        logger.error(f"❌ Error crítico en AccountingEngine para factura {instance.invoice_number}: {str(e)}", exc_info=True)
