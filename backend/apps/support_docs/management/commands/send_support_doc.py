from django.core.management.base import BaseCommand, CommandError
from apps.support_docs.models import SupportDocument
from apps.support_docs.services.dian_sender import SupportDocumentSender
import traceback

class Command(BaseCommand):
    help = 'Envía un Documento Soporte a la DIAN (Habilitación o Producción dependiendo de la config del Cliente)'

    def add_arguments(self, parser):
        parser.add_argument('doc_id', type=int, help='ID del Documento Soporte a enviar')

    def handle(self, *args, **options):
        doc_id = options['doc_id']
        
        self.stdout.write(self.style.WARNING(f'--- INICIANDO PROTOCOLO DE ENVÍO PARA DOCUMENTO ID: {doc_id} ---'))

        try:
            # 1. Buscar Documento
            try:
                doc = SupportDocument.objects.get(pk=doc_id)
            except SupportDocument.DoesNotExist:
                raise CommandError(f'El documento con ID {doc_id} no existe.')

            self.stdout.write(f"Documento encontrado: {doc.resolution.prefix}{doc.consecutive}")
            self.stdout.write(f"Cliente (Emisor): {doc.client.name} (NIT: {doc.client.nit})")
            
            if doc.client.dian_test_set_id:
                self.stdout.write(self.style.NOTICE(f"MODO: HABILITACION (TestSetID: {doc.client.dian_test_set_id})"))
            else:
                self.stdout.write(self.style.ERROR("MODO: PRODUCCION (Sin TestSetID - Cuidado!)"))

            if not doc.client.dian_certificate:
                self.stdout.write(self.style.ERROR("ADVERTENCIA CRÍTICA: El cliente no tiene certificado digital configurado. El envío fallará o no irá firmado."))

            # 2. Instanciar Sender
            sender = SupportDocumentSender(doc)

            # 3. Ejecutar Envío
            self.stdout.write("Generando XML, Firmando y Comprimiendo...")
            result = sender.send()

            # 4. Resultado
            if result:
                self.stdout.write(self.style.SUCCESS(f'✅ ENVÍO EXITOSO. Estado DIAN: {doc.dian_status}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ ENVÍO FALLIDO. Estado DIAN: {doc.dian_status}'))
                self.stdout.write("Revise los logs (debug_support_xml.py generaba logs en archivo, este comando usa stdout/logging django)")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'ERROR DE EJECUCIÓN: {str(e)}'))
            self.stdout.write(traceback.format_exc())
