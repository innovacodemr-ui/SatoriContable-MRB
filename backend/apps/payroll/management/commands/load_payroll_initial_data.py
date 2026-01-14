
from django.core.management.base import BaseCommand
from apps.payroll.models import LegalParameter, NoveltyType
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Carga datos iniciales de Nómina (Parámetros Legales y Tipos de Novedad)'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando carga de datos de nómina...")

        # 1. Datos para LegalParameter
        legal_parameters_data = [
            # --- SALARIO MÍNIMO & AUXILIO 2026 ---
            {
                "key": "SMMLV",
                "value": Decimal("1750905.00"),  # Valor proyectado 2026
                "valid_from": date(2026, 1, 1),
                "valid_to": date(2026, 12, 31)
            },
            {
                "key": "AUX_TRANS",
                "value": Decimal("249095.00"),
                "valid_from": date(2026, 1, 1),
                "valid_to": date(2026, 12, 31)
            },
            {
                "key": "UVT",
                "value": Decimal("53905.00"), # Proyección UVT 2026
                "valid_from": date(2026, 1, 1),
                "valid_to": date(2026, 12, 31)
            },

            # --- JORNADA LABORAL (EL CAMBIO AUTOMÁTICO) ---
            # Registro 1: Vigente hoy (Enero a Julio 14 de 2026)
            {
                "key": "MAX_WEEKLY_HOURS",
                "value": Decimal("44.00"),
                "valid_from": date(2025, 7, 16), 
                "valid_to": date(2026, 7, 14) # Termina el día antes del cambio
            },
            # Registro 2: Entra en vigor automáticamente el 15 de Julio
            {
                "key": "MAX_WEEKLY_HOURS",
                "value": Decimal("42.00"),
                "valid_from": date(2026, 7, 15),
                "valid_to": None # Indefinido hasta nuevo cambio
            },

            # --- RECARGO DOMINICAL (EL OTRO CAMBIO) ---
            # Registro 1: Vigente hoy (80%)
            {
                "key": "SURCHARGE_DOMINICAL", 
                "value": Decimal("0.80"),
                "valid_from": date(2025, 1, 1),
                "valid_to": date(2026, 6, 30)
            },
            # Registro 2: Sube al 90% (o 100% según reforma) en Julio
            {
                "key": "SURCHARGE_DOMINICAL",
                "value": Decimal("0.90"),
                "valid_from": date(2026, 7, 1),
                "valid_to": None
            }
        ]

        # 2. Datos para NoveltyType
        novelty_types_data = [
            {
                "code": "IGE_66",
                "name": "Incapacidad General (>2 días)",
                "dian_type": "IGE",
                "payroll_payment_percentage": Decimal("0.6667"), # Paga al 66.67%
                "affects_transport_aid": True,        # NO paga auxilio transporte
                "pays_health": True,                  # SÍ cotiza salud (IBC)
                "pays_pension": True,                 # SÍ cotiza pensión (IBC)
                "pays_arl": False                     # NO cotiza riesgos
            },
            {
                "code": "LNR",
                "name": "Licencia No Remunerada",
                "dian_type": "LNR",
                "payroll_payment_percentage": Decimal("0.0000"), # No paga sueldo
                "affects_transport_aid": True,        # NO paga auxilio
                "pays_health": False,                 # NO cotiza salud (generalmente)
                "pays_pension": True,                 # SÍ debe cotizar pensión
                "pays_arl": False                     # NO cotiza riesgos
            },
            {
                "code": "VAC",
                "name": "Vacaciones Disfrutadas",
                "dian_type": "VAC",
                "payroll_payment_percentage": Decimal("1.0000"), # Paga al 100% (Salario base)
                "affects_transport_aid": True,        # NO paga auxilio transporte
                "pays_health": True,                  # SÍ cotiza
                "pays_pension": True,                 # SÍ cotiza
                "pays_arl": False                     # NO cotiza riesgos (el riesgo cesa)
            },
            {
                "code": "LMA",
                "name": "Licencia Maternidad/Paternidad",
                "dian_type": "LMA",
                "payroll_payment_percentage": Decimal("1.0000"), # Paga 100% (Lo cubre EPS)
                "affects_transport_aid": True,        # NO paga auxilio
                "pays_health": True,                  # SÍ cotiza
                "pays_pension": True,                 # SÍ cotiza
                "pays_arl": False                     # NO cotiza
            }
        ]

        # Procesar LegalParameters
        self.stdout.write("--- Cargando Parámetros Legales ---")
        for data in legal_parameters_data:
            obj, created = LegalParameter.objects.update_or_create(
                key=data['key'],
                valid_from=data['valid_from'],
                defaults={
                    'value': data['value'],
                    'valid_to': data['valid_to']
                }
            )
            action = "Creado" if created else "Actualizado"
            self.stdout.write(f"{action}: {obj}")

        # Procesar NoveltyTypes
        self.stdout.write("\n--- Cargando Tipos de Novedades ---")
        for data in novelty_types_data:
            obj, created = NoveltyType.objects.update_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'dian_type': data['dian_type'],
                    'payroll_payment_percentage': data['payroll_payment_percentage'],
                    'affects_transport_aid': data['affects_transport_aid'],
                    'pays_health': data['pays_health'],
                    'pays_pension': data['pays_pension'],
                    'pays_arl': data['pays_arl']
                }
            )
            action = "Creado" if created else "Actualizado"
            self.stdout.write(f"{action}: {obj}")
        
        self.stdout.write(self.style.SUCCESS("¡Carga de datos completada exitosamente!"))
