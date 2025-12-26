from django.core.management.base import BaseCommand
from bills.models import Bill
from decimal import Decimal


class Command(BaseCommand):
    help = 'Convert existing bills to NPR based on exchange rates'

    def handle(self, *args, **kwargs):
        # Exchange rates to NPR
        exchange_rates = {
            'NPR': Decimal('1.0000'),
            'USD': Decimal('132.50'),
            'EUR': Decimal('145.00'),
            'GBP': Decimal('168.00'),
            'CAD': Decimal('95.00'),
            'AUD': Decimal('85.00'),
            'INR': Decimal('1.60'),
        }
        
        bills = Bill.objects.all()
        updated_count = 0
        
        for bill in bills:
            if bill.amount:
                # Get exchange rate
                rate = exchange_rates.get(bill.currency, Decimal('1.0000'))
                bill.exchange_rate = rate
                bill.amount_npr = bill.amount * rate
                bill.save(update_fields=['exchange_rate', 'amount_npr'])
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully converted {updated_count} bills to NPR'
            )
        )
