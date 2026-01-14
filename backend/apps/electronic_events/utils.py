import hashlib
from datetime import datetime

def generate_cude_sha384(
    event_id: str,
    issue_date: str,
    issue_time: str,
    event_code: str, # "030", "032", etc
    issuer_nit: str, # Quien emite el evento (Nosotros)
    receiver_nit: str, # Quien recibe (Proveedor)
    cufe: str,
    software_pin: str,
    environment: str # "1"=Prod, "2"=Pruebas
) -> str:
    """
    Calcula el CUDE (Código Único de Documento Electrónico) según Anexo Técnico DIAN.
    Fórmula: SHA-384(ID + Fecha + Hora + CodigoEvento + NitEmisor + DocReceptor + CUFE + Protocolo + Ambiente)
    Wait: La formula exacta para ApplicationResponse suele ser:
    CUDE = SHA-384(CdR + FecGen + HorGen + ValFac + CodImp + ValImp + ... + NitOFE + DocAdq + ClaveTecnica + TipoAmbiente) ???
    NO, eso es Factura. Para Eventos (ApplicationResponse) ver Numeral 11.2 Anexo Tecnico Eventos 2020:
    
    CUDE = SHA-384(ID + Fecha + Hora + CodigoEvento + NitEmisor + DocReceptor + CUFE + SoftwarePIN + Ambiente)
    
    Donde:
    - ID: Identificador del evento (ej: "AR123")
    - NitEmisor: Quien genera el evento (Nosotros)
    - DocReceptor: A quien va dirigido (Proveedor)
    """
    
    # Normalización
    # Fechas exactas como irán en XML?
    # Concatenación Estricta
    
    cude_seed = f"{event_id}{issue_date}{issue_time}{event_code}{issuer_nit}{receiver_nit}{cufe}{software_pin}{environment}"
    
    # Debug log (security awareness: careful logging pin)
    # print(f"CUDE SEED: {cude_seed}")
    
    return hashlib.sha384(cude_seed.encode('utf-8')).hexdigest()
