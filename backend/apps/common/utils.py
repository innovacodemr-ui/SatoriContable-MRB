from cryptography.fernet import Fernet
from django.conf import settings
import base64

class SecurityService:
    """
    Servicio de seguridad para manejo de secretos en la aplicación.
    Utiliza Fernet (implementación de criptografía simétrica) para cifrar y descifrar.
    """
    
    @staticmethod
    def _get_check_key():
        """Obtiene la clave de cifrado de settings o genera una temporal (solo dev)"""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Fallback inseguro solo para desarrollo si no está configurado
            # En producción esto debe venir de variable de entorno obligatoria
            return b'gH8x_t9X82t70w57482_xx8234-x8_x8234-x8_x8=' # Dummy 32 url-safe base64
        
        # Asegurar bytes
        if isinstance(key, str):
            key = key.encode()
        return key

    @staticmethod
    def encrypt_password(text_password: str) -> str:
        """
        Cifra una contraseña en texto plano.
        Retorna la cadena cifrada en base64 (string).
        """
        if not text_password:
            return ""
            
        key = SecurityService._get_check_key()
        f = Fernet(key)
        
        # Fernet encrypt espera bytes y retorna bytes
        encrypted_bytes = f.encrypt(text_password.encode('utf-8'))
        
        # Retornamos string para almacenamiento fácil en DB (CharField)
        return encrypted_bytes.decode('utf-8')

    @staticmethod
    def decrypt_password(encrypted_password: str) -> str:
        """
        Descifra una contraseña guardada.
        """
        if not encrypted_password:
            return ""
            
        key = SecurityService._get_check_key()
        f = Fernet(key)
        
        try:
            # Fernet decrypt espera bytes
            decrypted_bytes = f.decrypt(encrypted_password.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            # Si falla (ej. clave incorrecta o formato inválido), retornamos string vacío o lanzamos error
            print(f"Error descifrando: {e}")
            return ""
