from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
from apps.tenants.models import Client

class PayrollPDFService:
    @staticmethod
    def generate_payslip_pdf(payroll_document):
        """
        Genera el PDF del comprobante de nómina usando template HTML
        """
        # Obtener datos de la empresa (asumiendo single-tenant o tenant activo)
        # Si no hay tenant, usamos dummy
        try:
            company = Client.objects.first() or {
                'name': 'DEMO COMPANY S.A.S', 
                'nit': '900.000.000-1'
            }
        except:
            company = {'name': 'DEMO COMPANY S.A.S', 'nit': '900.000.000-1'}

        # Obtener detalles ordenados
        details = payroll_document.details.all().order_by('concept_type', 'id')
        
        context = {
            'document': payroll_document,
            'items': details,
            'company': company,
        }
        
        template = get_template('payroll/payslip.html')
        html = template.render(context)
        
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if pdf.err:
            return None
            
        return result.getvalue()
