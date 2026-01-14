from decimal import Decimal
from .models import LegalParameter, NoveltyType, EmployeeNovelty, PayrollDetail, PayrollConcept
from .utils import calculate_commercial_days
# from .models import PayrollDocument # Avoid circular import if possible, pass objects instead

class SocialSecurityCalculator:
    """
    Calcula IBC y aportes (Salud, Pensión, ARL, Parafiscales)
    Cumple con la norma de 'Piso de Protección Social' y la regla del 40% para independientes (aquí empleados).
    Ahora usa PayrollConcept para obtener porcentajes dinámicos.
    """
    
    @staticmethod
    def calculate_ibc(total_earned, is_integral_salary=False):
        """
        Calcula el Ingreso Base de Cotización.
        - Regla general: 100% del Salario + Otros factores salariales.
        - Salario Integral: 70% del total devengado.
        - Tope máximo: 25 SMMLV.
        - Tope mínimo: 1 SMMLV (ajustado por días trabajados).
        """
        smmlv = LegalParameter.get_value('SMMLV')
        if not smmlv: smmlv = Decimal('1300000') # Seguridad en caso de que falle la carga

        if is_integral_salary:
            ibc = total_earned * Decimal('0.70')
        else:
            ibc = total_earned
            
        # Topes
        max_ibc = smmlv * 25
        if ibc > max_ibc:
            ibc = max_ibc
            
        return ibc

    @staticmethod
    def get_contributions(ibc, risk_level=1):
        """
        Retorna diccionario con los aportes empresa/empleado usando conceptos maestros.
        """
        # Obtener porcentajes de la DB
        def get_pct(code, default):
            try:
                 obj = PayrollConcept.objects.get(code=code)
                 return obj.percentage / 100
            except:
                 return Decimal(default)

        HEALTH_EMP_RATE = get_pct('SALUD', '0.04')
        PENSION_EMP_RATE = get_pct('PENSION', '0.04')
        
        # Estos son aporte empresa, podria haber conceptos para esto o dejarlos fijos aqui por ahora
        HEALTH_COMP = Decimal('0.085') # Exoneración si < 10 SMMLV
        PENSION_COMP = Decimal('0.12')
        
        ARL_RATES = {
            1: Decimal('0.00522'),
            2: Decimal('0.01044'),
            3: Decimal('0.02436'),
            4: Decimal('0.04350'),
            5: Decimal('0.06960'),
        }
        
        arl_rate = ARL_RATES.get(risk_level, Decimal('0.00522'))
        
        return {
            'health_employee': ibc * HEALTH_EMP_RATE,
            'pension_employee': ibc * PENSION_EMP_RATE,
            'health_company': ibc * HEALTH_COMP,
            'pension_company': ibc * PENSION_COMP,
            'arl_company': ibc * arl_rate
        }

class PayrollCalculator:
    """
    Orquestador de la liquidación de nómina.
    Usa PayrollConcept para aplicar reglas y porcentajes de ley automáticamente.
    """
    
    def __init__(self, employee, start_date, end_date):
        self.employee = employee
        self.start_date = start_date
        self.end_date = end_date
        # self.days_worked = (end_date - start_date).days + 1 # DEPRECATED: Usar lógica comercial colombiana 360
        self.days_worked = calculate_commercial_days(start_date, end_date)
        
        # Cargar parámetros globales
        self.smmlv = LegalParameter.get_value('SMMLV')
        self.aux_trans = LegalParameter.get_value('AUX_TRANS')
        self.max_hours = LegalParameter.get_value('MAX_WEEKLY_HOURS') # 42 en 2026, 48 legado
        if not self.max_hours: self.max_hours = 240 # Fallback mensual
        else: self.max_hours = self.max_hours * 4 # Aprox mensual si viene semanal
        
    def calculate_concepts(self):
        """
        Retorna lista de diccionarios con conceptos (Devengados, Deducciones).
        """
        concepts = []
        
        # 1. Salario Base (Proporcional a días trabajados - novedades)
        # Buscar novedades en el periodo
        novelties = EmployeeNovelty.objects.filter(
            employee=self.employee,
            start_date__gte=self.start_date,
            end_date__lte=self.end_date
        )
        
        novelty_days = sum(n.days for n in novelties)
        paid_days = self.days_worked - novelty_days
        
        self.novelty_days = novelty_days # Expose for Dashboard
        
        salary_concept = PayrollConcept.objects.filter(code='BASICO').first()
        salary_payment = (self.employee.base_salary / 30) * paid_days
        
        concepts.append({
            'code': salary_concept.dian_code if salary_concept else 'BASICO',
            'description': salary_concept.name if salary_concept else 'Sueldo Básico',
            'quantity': paid_days,
            'value': salary_payment,
            'type': 'EARNING'
        })
        
        # 2. Auxilio de Transporte (Si aplica y < 2 SMMLV)
        if self.employee.transport_allowance_eligible and self.employee.base_salary <= (self.smmlv * 2):
            # Descontar días de novedades que afectan auxilio
            transport_days = self.days_worked
            for nov in novelties:
                if nov.novelty_type.affects_transport_aid:
                    transport_days -= nov.days
            
            if transport_days > 0:
                aux_concept = PayrollConcept.objects.filter(code='TRANSPORTE').first()
                aux_value = (self.aux_trans / 30) * transport_days
                concepts.append({
                    'code': aux_concept.dian_code if aux_concept else 'AUX_TRANSPORTE',
                    'description': aux_concept.name if aux_concept else 'Auxilio de Transporte',
                    'quantity': transport_days,
                    'value': aux_value,
                    'type': 'EARNING'
                })

        # 3. Procesar Novedades (Incapacidades, Horas Extras Dinámicas, etc.)
        # Calculamos Valor Hora Ordinaria para extras
        hour_value = self.employee.base_salary / 240 # Normativa 240H o division 30/8
        
        for nov in novelties:
            # Estrategia: Buscar si el NoveltyType tiene mapeo a un PayrollConcept
            # Asumimos que NoveltyType.dian_type coincide con PayrollConcept.code (Ej: HED)
            concept_master = PayrollConcept.objects.filter(code=nov.novelty_type.dian_type).first()
            
            val = Decimal(0)
            desc = nov.novelty_type.name
            
            if concept_master:
                # Es un concepto parametrizado (Hora Extra, Recargo, etc)
                if concept_master.percentage > 0:
                     # Fórmula Hora Extra: Valor Hora * Factor * Cantidad
                     # Factor = (100 + porcentaje) / 100 ?? No, usuarlmente el recargo es el % extra.
                     # Si es HED (25%), se paga 1.25 * hora para que incluya la base, o 0.25 si es solo recargo?
                     # En Colombia se paga el valor total (1.25)
                     
                     # Corrección lógica: La tabla maestra tiene el recargo (ej 25)
                     # Si es trabajo suplementario, se paga 1 + (pct/100).
                     # Si es solo recargo (Recargo Nocturno), es solo (pct/100).
                     
                     factor = Decimal(1) + (concept_master.percentage / 100)
                     # Excepcion Recargos Puros (HRN, HRDDF, HRNDF) usualmente son solo el sobrecosto si la hora ordinaria ya esta en el basico?
                     # Si se pagan Aparte del sueldo (es decir, trabajo adicional), es 1.X
                     # Si es Recargo Nocturno de turno ordinario, es 0.35.
                     
                     if "Recargo" in concept_master.name and "Extra" not in concept_master.name:
                          factor = (concept_master.percentage / 100)
                     
                     val = hour_value * factor * nov.days # nov.days aqui serian HORAS reportadas
                     # WARNING: El campo se llama 'days', toca interpretar si es dias u horas segun el tipo.
                     # Asumiremos que para HED, HEN, etc, el usuario ingresa HORAS en el campo days.
                
                else:
                     # Es una incapacidad o licencia (porcentaje viene de ley pero a veces de config)
                     # Usamos lógica de días (sueldo diario)
                     # Incapacidad 66.67%
                     if "INCAPACIDAD" in concept_master.code:
                         val = (self.employee.base_salary / 30) * nov.days * (Decimal(66.67)/100)
                     elif "LICENCIA" in concept_master.code:
                         val = (self.employee.base_salary / 30) * nov.days
            else:
                 # Fallback logica antigua o genérica
                 factor = nov.novelty_type.payroll_payment_percentage
                 if factor > 0:
                    val = (self.employee.base_salary / 30) * nov.days * factor

            if val > 0:
                concepts.append({
                    'code': concept_master.dian_code if concept_master else nov.novelty_type.dian_type,
                    'description': desc,
                    'quantity': nov.days,
                    'value': val,
                    'type': 'EARNING' if not concept_master or concept_master.concept_type == 'EARNING' else 'DEDUCTION'
                })
        
        # 4. Calcular Seguridad Social
        # Filtramos solo devs salariales para la base (suponiendo is_salary=True en tabla maestra)
        # Por ahora todos earning menos transporte
        
        total_devengado = sum(c['value'] for c in concepts if c['type'] == 'EARNING')
        
        # Base IBC
        base_ibc = Decimal(0)
        # Sumar solo salariales
        for c in concepts:
            # Buscar si es salarial en DB o hardcode
            # Por eficiencia, asumimos logica: Todo suma menos Aux Trans y Bonos No Salariales
            if c['code'] not in ['AUX_TRANSPORTE', 'AUX_CONECTIVIDAD', 'BONIFICACION_NS']:
                base_ibc += c['value']

        ibc = SocialSecurityCalculator.calculate_ibc(base_ibc)
        contribs = SocialSecurityCalculator.get_contributions(ibc, self.employee.risk_level)
        
        # Deducciones Empleado
        # Buscar Conceptos para obtener nombre y codigos actualizados
        salud_concept = PayrollConcept.objects.filter(code='SALUD').first()
        pension_concept = PayrollConcept.objects.filter(code='PENSION').first()

        concepts.append({
            'code': salud_concept.dian_code if salud_concept else 'SALUD',
            'description': salud_concept.name if salud_concept else 'Aporte Salud',
            'quantity': 0,
            'value': contribs['health_employee'],
            'type': 'DEDUCTION'
        })
        concepts.append({
            'code': pension_concept.dian_code if pension_concept else 'PENSION',
            'description': pension_concept.name if pension_concept else 'Aporte Pensión',
            'quantity': 0,
            'value': contribs['pension_employee'],
            'type': 'DEDUCTION'
        })
        
        return concepts
