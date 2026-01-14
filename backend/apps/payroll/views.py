from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db import transaction

from .models import LegalParameter, NoveltyType, EmployeeNovelty, Employee, PayrollPeriod, PayrollDocument, PayrollDetail
from .serializers import (
    LegalParameterSerializer, NoveltyTypeSerializer, EmployeeNoveltySerializer,
    EmployeeSerializer, PayrollPeriodSerializer, PayrollDocumentSerializer
)
from .services import PayrollCalculator
from .pdf_service import PayrollPDFService
from apps.dian.services import ElectronicPayrollBuilder
from apps.tenants.models import Client
from apps.common.utils import SecurityService
from django.conf import settings
import os
from django.http import HttpResponse

class LegalParameterViewSet(viewsets.ModelViewSet):
    serializer_class = LegalParameterSerializer

    def get_queryset(self):
        return LegalParameter.objects.all()

class NoveltyTypeViewSet(viewsets.ModelViewSet):
    serializer_class = NoveltyTypeSerializer

    def get_queryset(self):
        return NoveltyType.objects.all()

class EmployeeNoveltyViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeNoveltySerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser) 
    # Soporta subida de archivos y JSON estándar

    def get_queryset(self):
        return EmployeeNovelty.objects.all()

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        return Employee.objects.all()

class PayrollPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollPeriodSerializer

    def get_queryset(self):
        return PayrollPeriod.objects.all()

    @action(detail=True, methods=['post'])
    def liquidate(self, request, pk=None):
        """
        Liquidar la nómina para el periodo seleccionado.
        Calcula devengados y deducciones dinámicamente.
        """
        period = self.get_object()
        
        if period.status in ['PAID', 'REPORTED']:
            return Response({"error": "Periodo ya cerrado o pagado."}, status=400)

        employees = Employee.objects.filter(is_active=True)
        # TODO: Filtrar por fecha ingreso/retiro vs fechas periodo
        
        results = []
        
        try:
            with transaction.atomic():
                # Limpiar liquidaciones previas de este periodo (Borrador)
                PayrollDocument.objects.filter(period=period).delete()
                
                for emp in employees:
                    calculator = PayrollCalculator(emp, period.start_date, period.end_date)
                    concepts = calculator.calculate_concepts()
                    
                    # Totales
                    accrued = sum(c['value'] for c in concepts if c['type'] == 'EARNING')
                    deductions = sum(c['value'] for c in concepts if c['type'] == 'DEDUCTION')
                    net = accrued - deductions
                    
                    # Crear Documento
                    doc = PayrollDocument.objects.create(
                        period=period,
                        employee=emp,
                        cune=None, # Permitir multiples borradores sin CUNE
                        conseccutive=0, # TODO: Generar consecutivo
                        worked_days=calculator.days_worked - calculator.novelty_days, 
                        novelty_days=calculator.novelty_days,
                        accrued_total=accrued,
                        deductions_total=deductions,
                        net_total=net
                    )
                    
                    # Crear Detalles
                    for c in concepts:
                        PayrollDetail.objects.create(
                            document=doc,
                            concept_type=c['type'],
                            dian_code=c['code'],
                            description=c['description'],
                            quantity=c['quantity'],
                            value=c['value']
                        )
                    
                    results.append({
                        "employee": emp.code,
                        "document_id": doc.id,
                        "net": net,
                        "worked_days": doc.worked_days,
                        "novelty_days": doc.novelty_days,
                        "accrued": doc.accrued_total,
                        "deductions": doc.deductions_total,
                        "employee_name": f"{emp.third_party.first_name} {emp.third_party.surname}",
                        "position": emp.position,
                        "dian_status": doc.dian_status
                    })
                
                period.status = 'LIQUIDATED'
                period.save()
                
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        return Response({"message": "Liquidación completada", "results": results})

class PayrollDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollDocumentSerializer

    def get_queryset(self):
        return PayrollDocument.objects.all()

    @action(detail=True, methods=['get'])
    def download_payslip(self, request, pk=None):
        document = self.get_object()
        try:
            pdf_content = PayrollPDFService.generate_payslip_pdf(document)
            
            if not pdf_content:
                return Response({'error': 'Error generando PDF'}, status=500)

            response = HttpResponse(pdf_content, content_type='application/pdf')
            # Fix: PayrollPeriod uses 'name' or 'id', not 'code'
            filename = f"payslip_{document.period.id}_{document.employee.code}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=500)

    @action(detail=True, methods=['post'])
    def transmit(self, request, pk=None):
        """
        Transmite el documento a la DIAN.
        Firma XML -> Empaqueta -> Envía -> Actualiza Estado.
        """
        document = self.get_object()
        
        if document.dian_status == 'ACCEPTED':
             return Response({"message": "Documento ya aceptado por DIAN."}, status=400)

        # 1. Obtener Configuración de Empresa (Multi-tenant MVP)
        company = Client.objects.first()
        if not company:
             return Response({"error": "No hay empresa configurada."}, status=500)

        # 2. Obtener Certificado
        cert_data = None
        cert_password = None

        if company.dian_certificate:
            # Usar certificado de la DB
            try:
                cert_data = company.dian_certificate.read()
                # Descifrar contraseña
                encrypted_pass = company.certificate_password_encrypted
                # Fallback temporal para legacy o desarrollo
                if not encrypted_pass and company.dian_certificate_password:
                     cert_password = company.dian_certificate_password
                else: 
                     cert_password = SecurityService.decrypt_password(encrypted_pass)

                if not cert_password:
                     return Response({"error": "No se pudo descifrar la contraseña del certificado."}, status=500)

            except Exception as e:
                return Response({"error": f"Error leyendo certificado DB: {str(e)}"}, status=500)
        else:
            # Fallback a archivo local (Solo Dev)
            cert_path = os.path.join(settings.BASE_DIR, 'apps', 'dian', 'certs', 'certificate.p12')
            if os.path.exists(cert_path):
                cert_data = cert_path
                cert_password = "Satori2026"
            else:
                 return Response({"error": "Certificado digital no encontrado (ni en DB ni local)."}, status=500)
            
        try:
            builder = ElectronicPayrollBuilder()
            
            # Proceso Completo (Pasamos company explícitamente)
            result = builder.transmit_document(document, cert_data, cert_password, company)
            
            # Guardar XML Firmado (Simulado guardado en archivo o DB)
            # En producción, guardar result['signed_xml'] en document.xml_file
            
            # Analizar Respuesta
            soap_response = result['soap_response']
            document.dian_response = soap_response.text
            
            # Validar éxito (Simplificado)
            if soap_response.status_code == 200 and "TrackId" in soap_response.text:
                document.dian_status = 'SENT'
            else:
                document.dian_status = 'REJECTED'
            
            document.save()
            
            return Response({
                "message": "Transmisión realizada", 
                "dian_status": document.dian_status,
                "dian_response": document.dian_response[:500] # Primeros caracteres
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
