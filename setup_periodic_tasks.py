import os
import django

# Setup Django FIRST before importing models that access settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django_celery_beat.models import PeriodicTask, IntervalSchedule

# Create 5-minute interval
schedule, created = IntervalSchedule.objects.get_or_create(
    every=5,
    period=IntervalSchedule.MINUTES,
)

# Create the periodic task
task, created = PeriodicTask.objects.get_or_create(
    name='Check DIAN Emails (5 min)',
    defaults={
        'interval': schedule,
        'task': 'apps.electronic_events.tasks.check_new_dian_emails',
    }
)

if created:
    print(f"Created new periodic task: {task.name}")
else:
    task.interval = schedule
    task.task = 'apps.electronic_events.tasks.check_new_dian_emails'
    task.save()
    print(f"Updated existing periodic task: {task.name}")

# Create daily interval
daily_schedule, created = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.DAYS,
)

# Create the periodic task for certificate expiration
cert_task, created = PeriodicTask.objects.get_or_create(
    name='Check Certificate Expiration (Daily)',
    defaults={
        'interval': daily_schedule,
        'task': 'apps.health_checks.tasks.check_certificate_expiration',
    }
)

if created:
    print(f"Created new periodic task: {cert_task.name}")
else:
    cert_task.interval = daily_schedule
    cert_task.task = 'apps.health_checks.tasks.check_certificate_expiration'
    cert_task.save()
    print(f"Updated existing periodic task: {cert_task.name}")
