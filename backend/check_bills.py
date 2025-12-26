import os
import django
import traceback

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'majorproject.settings')
    django.setup()

    from bills.models import Bill
    from django.db.models import Q

    print("Starting query for valid bills...")
    valid_bills = Bill.objects.filter(
        Q(amount_npr__isnull=False) & ~Q(account_type='')
    )
    print(f"Valid bills count: {valid_bills.count()}")
    print("Query completed successfully.")
except Exception as e:
    print("An error occurred:")
    traceback.print_exc()