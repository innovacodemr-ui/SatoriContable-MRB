from django.core.management.base import BaseCommand
from apps.accounting.models import DianFormat, DianConcept

class Command(BaseCommand):
    help = 'Carga datos iniciales de Formatos y Conceptos DIAN (Exógena)'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando carga de datos DIAN...")

        # Definimos los datos (basado en lo que proporcionaste, ajustado)
        # Asumimos valid_from = 2025 para este ejemplo.
        VALID_FROM_YEAR = 2025

        formats_data = [
            { "pk": 1, "code": "1001", "name": "Pagos o abonos en cuenta y retenciones", "version": 10 },
            { "pk": 2, "code": "1003", "name": "Retenciones en la fuente que le practicaron", "version": 7 },
            { "pk": 3, "code": "1005", "name": "Impuesto a las ventas por pagar (Descontable)", "version": 7 },
            { "pk": 4, "code": "1006", "name": "Impuesto a las ventas generado", "version": 8 },
            { "pk": 5, "code": "1007", "name": "Ingresos recibidos", "version": 9 },
            { "pk": 6, "code": "1008", "name": "Saldo de Cuentas por Cobrar", "version": 7 },
            { "pk": 7, "code": "1009", "name": "Saldo de Cuentas por Pagar", "version": 7 },
            { "pk": 8, "code": "2276", "name": "Rentas de trabajo y pensiones", "version": 4 },
        ]

        # Mapeo de concepts usando el PK del formato del JSON original para referencia
        concepts_data = [
            # Formato 1001 (pk 1)
            { "format_pk": 1, "code": "5001", "name": "Salarios, prestaciones y demás pagos laborales" },
            { "format_pk": 1, "code": "5002", "name": "Honorarios" },
            { "format_pk": 1, "code": "5003", "name": "Comisiones" },
            { "format_pk": 1, "code": "5004", "name": "Servicios" },
            { "format_pk": 1, "code": "5005", "name": "Arrendamientos" },
            { "format_pk": 1, "code": "5006", "name": "Intereses y rendimientos financieros" },
            { "format_pk": 1, "code": "5007", "name": "Compra de activos movibles" },
            { "format_pk": 1, "code": "5008", "name": "Otros costos y deducciones" },
            { "format_pk": 1, "code": "5010", "name": "Seguros" },
            { "format_pk": 1, "code": "5011", "name": "Compras de activos fijos" },
            { "format_pk": 1, "code": "5012", "name": "Servicios públicos" },
            
            # Formato 1003 (pk 2)
            { "format_pk": 2, "code": "1301", "name": "Retención por salarios y pagos laborales" },
            { "format_pk": 2, "code": "1302", "name": "Retención por ventas" },
            { "format_pk": 2, "code": "1303", "name": "Retención por servicios" },
            { "format_pk": 2, "code": "1304", "name": "Retención por honorarios" },

            # Formato 1007 (pk 5)
            { "format_pk": 5, "code": "4001", "name": "Ingresos brutos operacionales" },
            { "format_pk": 5, "code": "4002", "name": "Ingresos brutos no operacionales" },
            { "format_pk": 5, "code": "4003", "name": "Intereses y rendimientos financieros" },

            # Formato 1008 (pk 6)
            { "format_pk": 6, "code": "1315", "name": "Clientes" },
            { "format_pk": 6, "code": "1316", "name": "Cuentas por cobrar a socios y accionistas" },
            { "format_pk": 6, "code": "1317", "name": "Anticipos y avances entregados" },

            # Formato 1009 (pk 7)
            { "format_pk": 7, "code": "2201", "name": "Proveedores" },
            { "format_pk": 7, "code": "2202", "name": "Obligaciones financieras" },
            { "format_pk": 7, "code": "2206", "name": "Pasivos laborales" },

            # Formato 2276 (pk 8)
            { "format_pk": 8, "code": "1001", "name": "Pagos por salarios" },
            { "format_pk": 8, "code": "1008", "name": "Prestaciones sociales" },
            { "format_pk": 8, "code": "1011", "name": "Viáticos permanentes" },
            { "format_pk": 8, "code": "1016", "name": "Aportes obligatorios a salud (trabajador)" },
            { "format_pk": 8, "code": "1015", "name": "Aportes obligatorios a pensión (trabajador)" },
        ]

        # 1. Crear Formatos
        pk_map = {} # Para mapear pk original -> objeto real creado/encontrado
        
        for fmt in formats_data:
            obj, created = DianFormat.objects.update_or_create(
                code=fmt['code'],
                version=fmt['version'],
                valid_from=VALID_FROM_YEAR,
                defaults={
                    'name': fmt['name']
                }
            )
            pk_map[fmt['pk']] = obj
            
            status = "Creado" if created else "Actualizado"
            self.stdout.write(f"{status} Formato: {obj}")

        # 2. Crear Conceptos
        for cpt in concepts_data:
            if cpt['format_pk'] not in pk_map:
                self.stdout.write(self.style.WARNING(f"Format PK {cpt['format_pk']} no encontrado para concepto {cpt['code']}"))
                continue
                
            dian_format = pk_map[cpt['format_pk']]
            
            obj, created = DianConcept.objects.update_or_create(
                format=dian_format,
                code=cpt['code'],
                defaults={
                    'name': cpt['name']
                }
            )
            # status = "Creado" if created else "Existed"
            # self.stdout.write(f"  - Concepto {obj.code}")

        self.stdout.write(self.style.SUCCESS("Datos DIAN cargados exitosamente."))
