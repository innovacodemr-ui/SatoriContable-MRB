import sys
import os
import django
from decimal import Decimal
from datetime import date

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payroll.models import Employee, PayrollPeriod, PayrollDocument, EmployeeNovelty, NoveltyType, PayrollConcept
from apps.payroll.services import PayrollCalculator

# Debug: Check PayrollConcept
hed_concept = PayrollConcept.objects.filter(code='HED').first()
if not hed_concept:
    print("CRITICAL ERROR: PayrollConcept 'HED' NOT FOUND in DB!")
    # Attempt to load it just for this validaton? No, diagnosing.
    all_concepts = list(PayrollConcept.objects.values_list('code', flat=True))
    print(f"Available concepts: {all_concepts}")
else:
    print(f"Verified PayrollConcept 'HED' exists. Percentage: {hed_concept.percentage}")

# 1. Setup Employee
# Use 'Ana' or create one
emp = Employee.objects.filter(third_party__first_name__icontains='Ana').first()
if not emp:
    print("Ana not found, using first available.")
    emp = Employee.objects.first()

if not emp:
    print("No employees found.")
    sys.exit(1)

# Set salary to 2,400,000 for the test
old_salary = emp.base_salary
emp.base_salary = Decimal("2400000.00")
emp.save()
print(f"Using Employee: {emp.third_party.first_name} {emp.third_party.surname}, Salary: {emp.base_salary}")

# 2. Setup Period
period_name = "Test Validation Sept 2026"
start_date = date(2026, 9, 1)
end_date = date(2026, 9, 30)

period, created = PayrollPeriod.objects.get_or_create(
    name=period_name,
    defaults={
        'start_date': start_date,
        'end_date': end_date,
        'payment_date': end_date,
        'status': 'DRAFT'
    }
)
print(f"Using Period: {period.name}")

# 3. Create Novelty (HED)
# Ensure NoveltyType exists and matches PayrollConcept code 'HED'
hed_type = NoveltyType.objects.filter(dian_type='HED').first()
if not hed_type:
    print("Creating NoveltyType HED...")
    hed_type = NoveltyType.objects.create(
        name="Hora Extra Diurna",
        code="HED_TEST",
        dian_type="HED",
        payroll_payment_percentage=1.25
    )

# Clear existing novelties for this period/employee to be clean
EmployeeNovelty.objects.filter(employee=emp, start_date__gte=start_date, end_date__lte=end_date).delete()

# Create the 4 hours HED
EmployeeNovelty.objects.create(
    employee=emp,
    novelty_type=hed_type,
    start_date=start_date, 
    end_date=start_date,
    days=4 # usage: hours
)
print("Created Novelty: HED - 4 Hours")

# 4. Run Liquidation Logic
calculator = PayrollCalculator(emp, start_date, end_date)
concepts = calculator.calculate_concepts()

# 5. Verify Results
found_hed = False
for c in concepts:
    if c['code'] == 'HED':
        found_hed = True
        print(f"Found HED Result: Quantity={c['quantity']}, Value={c['value']}")
        
        expected_hourly = Decimal("2400000") / 240 # 10,000
        expected_value = expected_hourly * Decimal("1.25") * 4 # 50,000
        
        # Round 2 decimals
        val = round(c['value'], 2)
        expected = round(expected_value, 2)
        
        if val == expected:
             print(f"SUCCESS: Calculation matches exactly (${expected:,.2f}).")
        else:
             print(f"FAILURE: Expected {expected:,.2f}, got {val:,.2f}")

if not found_hed:
    print("FAILURE: HED Concept not found in liquidation results.")
    print("All Concepts:", [(x['code'], x['value']) for x in concepts])

# Restore salary
emp.base_salary = old_salary
emp.save()
print("Restored original salary.")
