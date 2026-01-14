from datetime import date, timedelta
import calendar

def calculate_commercial_days(start_date: date, end_date: date) -> int:
    """
    Calcula los días comerciales (base 360) entre dos fechas para nómina colombiana.
    
    Reglas:
    - Meses de 31 días: El día 31 se asume incluido en el 30.
    - Febrero: Si se trabaja completo (1-28/29), son 30 días.
    - Quincena 2 (16-31): Son 15 días.
    
    Fórmula general: (Year2 * 360 + Month2 * 30 + Day2) - (Year1 * 360 + Month1 * 30 + Day1) + 1
    """
    if start_date > end_date:
        return 0

    year1, month1, day1 = start_date.year, start_date.month, start_date.day
    year2, month2, day2 = end_date.year, end_date.month, end_date.day

    # Ajuste día 31 para fecha fin -> se vuelve 30
    if day2 == 31:
        day2 = 30
    
    # Ajuste día 31 para fecha inicio, si aplica (casos raros de ingreso el 31) -> se vuelve 30
    if day1 == 31:
        day1 = 30
        
    # Caso especial Febrero
    if month2 == 2:
        last_day_feb = calendar.monthrange(year2, month2)[1]
        if day2 == last_day_feb:
            # Si termina el último día de febrero
            if month1 == 2 and day1 == 1:
                # Si trabajó todo el mes -> 30 días
                return 30
            else:
                # Si es fracción de febrero, NO ajustamos day2 a 30.
                # Se pagan los días calendario efectivamente trabajados.
                # Ej: 28/02 al 28/02 -> 1 día. (Si ajustáramos a 30, daría 30-28+1=3, incorrecto)
                # Ej: 15/02 al 28/02 -> 14 días. (Si ajustáramos a 30, daría 30-15+1=16, incorrecto)
                pass

    # Fórmula Contable 360
    days = (year2 * 360 + month2 * 30 + day2) - (year1 * 360 + month1 * 30 + day1) + 1
    
    return days
