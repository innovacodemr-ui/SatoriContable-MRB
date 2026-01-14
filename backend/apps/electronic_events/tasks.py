from celery import shared_task
from .services.email_service import EmailReceptionService
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_new_dian_emails():
    """
    Tarea periódica para verificar nuevos correos de facturación electrónica.
    Se ejecuta en segundo plano (Celery Beat).
    """
    logger.info("Auto-Sync: Iniciando verificación de correos DIAN...")
    try:
        service = EmailReceptionService()
        result = service.fetch_invoices()
        
        if result['processed'] > 0:
            logger.info(f"Auto-Sync: Se procesaron {result['processed']} nuevas facturas.")
        elif result['errors'] > 0:
            logger.warning(f"Auto-Sync: Finalizó con {result['errors']} errores.")
        else:
            logger.info("Auto-Sync: No se encontraron nuevas facturas.")
            
        return f"Processed: {result['processed']}, Errors: {result['errors']}"
    except Exception as e:
        logger.error(f"Auto-Sync Error: {str(e)}")
        return f"Error: {str(e)}"
