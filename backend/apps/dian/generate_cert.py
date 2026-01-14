from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime
import os

def generate_self_signed_cert(filename="certificate.p12", password=b"Satori2026"):
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Generate a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"CO"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Valle del Cauca"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Cali"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Satori Software SAS"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"Satori Test Cert"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Valid for 1 year
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None), critical=True,
    ).sign(key, hashes.SHA256())

    # Write PKCS12
    p12 = pkcs12.serialize_key_and_certificates(
        name=b"Satori Key",
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(password)
    )

    with open(filename, "wb") as f:
        f.write(p12)
    
    print(f"Certificado generado exitosamente: {os.path.abspath(filename)}")
    print(f"Contrasena: {password.decode()}")

if __name__ == "__main__":
    # Save in a 'certs' directory inside dian app
    target_dir = os.path.join(os.path.dirname(__file__), "certs")
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "certificate.p12")
    generate_self_signed_cert(target_file)
