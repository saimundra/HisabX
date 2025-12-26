from django.core.management.base import BaseCommand
from bills.models import Bill
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Fix bills from user own company to be marked as REVENUE (CREDIT) instead of EXPENSE (DEBIT)'

    def handle(self, *args, **kwargs):
        fixed_count = 0
        
        # Get all users
        users = CustomUser.objects.all()
        
        for user in users:
            if not user.company_name:
                continue
            
            # Normalize company name for comparison
            company_normalized = user.company_name.strip().lower()
            
            # Find bills where vendor matches user's company name
            bills = Bill.objects.filter(user=user)
            
            for bill in bills:
                if bill.vendor:
                    vendor_normalized = bill.vendor.strip().lower()
                    
                    # Check if vendor matches company name
                    if vendor_normalized == company_normalized or company_normalized in vendor_normalized:
                        # This is user's own company - should be REVENUE/CREDIT
                        if bill.transaction_type != 'CREDIT':
                            bill.transaction_type = 'CREDIT'
                            bill.account_type = 'REVENUE'
                            bill.is_debit = False
                            bill.save(update_fields=['transaction_type', 'account_type', 'is_debit'])
                            fixed_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'Fixed bill ID {bill.id}: "{bill.vendor}" → REVENUE (CREDIT)'
                                )
                            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully fixed {fixed_count} bills to REVENUE (CREDIT)'
            )
        )
