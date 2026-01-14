from django.test import TestCase
from decimal import Decimal
from datetime import date
from apps.accounting.models import ThirdParty
from apps.payroll.models import Employee, NoveltyType, EmployeeNovelty, LegalParameter
from apps.payroll.services import PayrollCalculator

class LiquidationEngineIntegrationTest(TestCase):
    
    def setUp(self):
        # 1. Configurar Parámetros Legales (2026)
        LegalParameter.objects.create(
            key='SMMLV',
            value=Decimal('1300000.00'), # Valor base para testing
            valid_from=date(2026, 1, 1)
        )
        LegalParameter.objects.create(
            key='AUX_TRANS',
            value=Decimal('140606.00'),
            valid_from=date(2026, 1, 1)
        )

        # 2. Crear Tercero (Ana Gómez)
        self.third_party = ThirdParty.objects.create(
            party_type="EMPLEADO",
            person_type=2,
            first_name="Ana",
            surname="Gómez",
            identification_number="987654321",
            identification_type="13",
            is_active=True
        )

        # 3. Crear Empleado (Salario 3M)
        self.employee = Employee.objects.create(
            third_party=self.third_party,
            code="EMP_002",
            contract_type="INDEFINIDO",
            start_date=date(2025, 1, 1),
            base_salary=Decimal('3000000.00'),
            health_entity="Sura",
            pension_entity="Protección",
            severance_entity="Porvenir",
            arl_entity="Sura",
            risk_level=1,
            transport_allowance_eligible=True # Aunque por salario no le toque, el flag está activo
        )

        # 4. Configurar Tipo de Novedad (IGE_66)
        self.ige_type = NoveltyType.objects.create(
            code="IGE_66",
            name="Incapacidad General > 2 Días",
            dian_type="IGE",
            payroll_payment_percentage=Decimal('0.6667'),
            affects_transport_aid=True,
            pays_health=True,
            pays_pension=True
        )

        # 5. Crear la Novedad (3 Días: Ago 1 - Ago 3)
        EmployeeNovelty.objects.create(
            employee=self.employee,
            novelty_type=self.ige_type,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 3),
            days=3
        )

    def test_liquidation_scenario_august_2026(self):
        """
        Escenario: Ana Gómez, Salario 3M, 3 días Incapacidad General.
        Validar:
        - Días trabajados: 27
        - Valor Salario: 2.7M
        - Valor Incapacidad: ~200k
        - IBC y Seguridad Social correctos.
        """
        # Ejecutar Motor de Liquidación (1 al 30 de Agosto)
        calculator = PayrollCalculator(
            employee=self.employee,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 30)
        )
        
        concepts = calculator.calculate_concepts()
        
        # Convertir lista de conceptos a diccionario para facilitar asserts
        # key: code, value: dict completo
        concepts_map = {c['code']: c for c in concepts}

        # --- A. Validar Salario (27 Días) ---
        self.assertIn('BASICO', concepts_map)
        salary = concepts_map['BASICO']
        self.assertEqual(salary['quantity'], 27)
        self.assertEqual(salary['value'], Decimal('2700000.00')) # 3M / 30 * 27

        # --- B. Validar Incapacidad (3 Días al 66.67%) ---
        # El código será el dian_type ('IGE')
        self.assertIn('IGE', concepts_map)
        novelty = concepts_map['IGE']
        self.assertEqual(novelty['quantity'], 3)
        
        # Esperado: (3,000,000 / 30) * 3 * 0.6667 = 100,000 * 3 * 0.6667 = 200,010
        expected_incapacity = Decimal('200010.00') 
        self.assertAlmostEqual(novelty['value'], expected_incapacity, delta=Decimal('0.1'))

        # --- C. Validar Total Devengado (IBC) ---
        total_devengado = sum(c['value'] for c in concepts if c['type'] == 'EARNING')
        expected_devengado = Decimal('2700000.00') + expected_incapacity # 2,900,010
        self.assertEqual(total_devengado, expected_devengado)

        # --- D. Validar Salud y Pensión (4% del IBC) ---
        # IBC = Total Devengado (3M > 2 SMMLV, no hay aux transporte)
        expected_ibc = expected_devengado
        expected_deduction = expected_ibc * Decimal('0.04') # 116,000.40

        self.assertIn('SALUD', concepts_map)
        self.assertIn('PENSION', concepts_map)
        
        health_deduction = concepts_map['SALUD']['value']
        pension_deduction = concepts_map['PENSION']['value']

        self.assertAlmostEqual(health_deduction, expected_deduction, delta=Decimal('0.1'))
        self.assertAlmostEqual(pension_deduction, expected_deduction, delta=Decimal('0.1'))
        
        # --- E. Neto a Pagar ---
        total_deductions = health_deduction + pension_deduction
        net_pay = total_devengado - total_deductions
        
        expected_net = Decimal('2900010.00') - (Decimal('116000.40') * 2) 
        # 2,900,010 - 232,000.80 = 2,668,009.20
        
        print(f"\n--- RESULTADOS LIQUIDACIÓN ANA GÓMEZ ---")
        print(f"Salario (27d): {salary['value']}")
        print(f"Incapacidad (3d): {novelty['value']}")
        print(f"IBC: {expected_ibc}")
        print(f"Salud: {health_deduction}")
        print(f"Pensión: {pension_deduction}")
        print(f"Neto: {net_pay}")
        print(f"----------------------------------------")
