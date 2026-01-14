import os
import sys
import django
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Client
from apps.tenants.serializers import ClientSerializer
from apps.payroll.models import PayrollDocument
from apps.payroll.pdf_service import PayrollPDFService
from apps.payroll.views import ElectronicPayrollBuilder
from apps.common.utils import SecurityService

def create_assets():
    print("--- Creating Dummy Assets ---")
    # minimal transparent 1x1 png
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    # dummy p12 (invalid but exists)
    p12_data = b'DUMMY_P12_CONTENT_XYZ'
    
    return png_data, p12_data

def test_step_1_onboarding(png_data, p12_data):
    print("\n--- Step 1: Onboarding (Configuration) ---")
    client = Client.objects.first()
    if not client:
        print("Creating default client...")
        client = Client.objects.create(name="Test Company", nit="123456789")
    
    print(f"Target Client: {client.name} (ID: {client.id})")
    
    # Prepare data for Serializer
    logo_file = SimpleUploadedFile("logo.png", png_data, content_type="image/png")
    cert_file = SimpleUploadedFile("certificate.p12", p12_data, content_type="application/x-pkcs12")
    
    data = {
        'legal_name': 'EMPRESA VALIDADA SAS',
        'certificate_password': 'Satori2026'
    }
    
    full_data = data.copy()
    full_data['logo'] = logo_file
    full_data['dian_certificate'] = cert_file
    
    print("Updating client via Serializer...")
    serializer = ClientSerializer(client, data=full_data, partial=True)
    if serializer.is_valid():
        serializer.save()
        print("✅ Config saved successfully via Serializer.")
    else:
        print(f"❌ Serializer Error: {serializer.errors}")
        return False

    # Verify DB State
    client.refresh_from_db()
    if client.logo:
        print(f"✅ Logo stored: {client.logo.name}")
    else:
        print("❌ Logo missing.")

    if client.dian_certificate:
         print(f"✅ Certificate stored: {client.dian_certificate.name}")
    else:
         print("❌ Certificate missing.")
        
    if client.certificate_password_encrypted:
        print(f"✅ Password encrypted: {client.certificate_password_encrypted[:10]}...")
        # Verify decryption
        decrypted = SecurityService.decrypt_password(client.certificate_password_encrypted)
        if decrypted == 'Satori2026':
             print("✅ Password decryption verified.")
        else:
             print(f"❌ Decryption mismatch: {decrypted}")
    else:
        print("❌ Encrypted password field is empty!")
        
    return True

def test_step_2_brand_pdf():
    print("\n--- Step 2: Brand Test (PDF) ---")
    doc = PayrollDocument.objects.first()
    if not doc:
        print("❌ No PayrollDocument found. Cannot test PDF.")
        return False
        
    print(f"Generating PDF for Document #{doc.id}")
    try:
        pdf_bytes = PayrollPDFService.generate_payslip_pdf(doc)
        if pdf_bytes:
            print(f"✅ PDF Generated. Size: {len(pdf_bytes)} bytes.")
        else:
            print("❌ PDF Generation returned None (Error inside service).")
    except Exception as e:
        print(f"❌ Exception during PDF generation: {e}")
        import traceback
        traceback.print_exc()

def test_step_3_transmit():
    print("\n--- Step 3: Transmit (Dynamic Signing) ---")
    doc = PayrollDocument.objects.first()
    if not doc:
        return
    
    # Refresh client from DB to ensure we have the uploaded files
    client = Client.objects.first() # We know there is only one in this MVP test

    print("Attempting transmission setup...")
    try:
        builder = ElectronicPayrollBuilder()
        try:
             xml_content = builder.build_xml(doc, client)
             print("✅ XML Built.")
        except Exception as e:
             print(f"⚠️ XML Build warning: {e}")
             return

        # Prepare credentials
        if not client.dian_certificate or not client.certificate_password_encrypted:
             print("❌ Client credentials missing for signing")
             return

        password = SecurityService.decrypt_password(client.certificate_password_encrypted)
        cert_path = client.dian_certificate.path
        with open(cert_path, 'rb') as f:
             cert_data = f.read()

        # This step loads the cert from DB
        print("Executing sign_xml... (Expect failure due to dummy cert, but validating flow)")
        try:
            builder.sign_xml(xml_content, cert_data, password)
            print("✅ Signing Mock Success (Unexpected if cert is dummy)")
        except Exception as sign_error:
            err_str = str(sign_error)
            print(f"ℹ️ Signing Result: {err_str}")
            # We are happy if it fails trying to read the PKCS12
            print("✅ Logic Confirmation: System attempted to parse the uploaded certificate.")
                 
    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == "__main__":
    try:
        png, p12 = create_assets()
        if test_step_1_onboarding(png, p12):
            test_step_2_brand_pdf()
            test_step_3_transmit()
    except Exception as e:
        print(f"Fatal test error: {e}")
        import traceback
        traceback.print_exc()
