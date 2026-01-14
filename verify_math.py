from datetime import date
from backend.apps.payroll.utils import calculate_commercial_days

def test_logic():
    # Caso A: 01/05 al 15/05 -> 15 días
    d_a = calculate_commercial_days(date(2026, 5, 1), date(2026, 5, 15))
    print(f"Caso A (Expected 15): {d_a}")

    # Caso B: 16/05 al 31/05 -> 15 días
    d_b = calculate_commercial_days(date(2026, 5, 16), date(2026, 5, 31))
    print(f"Caso B (Expected 15): {d_b}")

    # Caso C: 01/05 al 31/05 -> 30 días
    d_c = calculate_commercial_days(date(2026, 5, 1), date(2026, 5, 31))
    print(f"Caso C (Expected 30): {d_c}")
    
    # Caso Febrero Bisiesto: 01/02/2024 (bisiesto) al 29/02/2024 -> 30 días
    d_feb = calculate_commercial_days(date(2024, 2, 1), date(2024, 2, 29))
    print(f"Caso Feb Bisiesto (Expected 30): {d_feb}")

    # Caso Febrero Normal: 01/02/2023 al 28/02/2023 -> 30 días
    d_feb2 = calculate_commercial_days(date(2023, 2, 1), date(2023, 2, 28))
    print(f"Caso Feb Normal (Expected 30): {d_feb2}")

if __name__ == "__main__":
    test_logic()
