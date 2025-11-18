from django.core.management.base import BaseCommand
from bills.models import Bill
from ocr.utils.ocr_processor import extract_invoice_number
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re-extract invoice numbers from existing bills OCR text'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-extract all bills, even those with invoice numbers',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of bills to process',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Re-extracting Invoice Numbers'))
        self.stdout.write('=' * 80)
        
        # Get bills to process
        if options['force']:
            bills = Bill.objects.all()
            self.stdout.write(f'Processing ALL {bills.count()} bills (--force enabled)')
        else:
            # Only process bills without invoice numbers
            bills = Bill.objects.filter(invoice_number__isnull=True) | Bill.objects.filter(invoice_number='')
            self.stdout.write(f'Processing {bills.count()} bills without invoice numbers')
        
        if options['limit']:
            bills = bills[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} bills\n')
        
        processed = 0
        updated = 0
        failed = 0
        
        for bill in bills:
            try:
                if not bill.ocr_text:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Bill #{bill.id} | No OCR text | Skipped'
                        )
                    )
                    continue
                
                old_invoice = bill.invoice_number or 'None'
                
                # Extract invoice number from OCR text
                invoice_number = extract_invoice_number(bill.ocr_text)
                
                if invoice_number:
                    bill.invoice_number = invoice_number
                    bill.save(update_fields=['invoice_number'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Bill #{bill.id} | '
                            f'Vendor: {bill.vendor or "N/A":<25} | '
                            f'{old_invoice} → {invoice_number}'
                        )
                    )
                    updated += 1
                else:
                    self.stdout.write(
                        f'  Bill #{bill.id} | '
                        f'Vendor: {bill.vendor or "N/A":<25} | '
                        f'No invoice number found in OCR text'
                    )
                
                processed += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Bill #{bill.id} | Error: {str(e)}'
                    )
                )
                failed += 1
        
        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.SUCCESS('RE-EXTRACTION COMPLETE'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total bills processed: {processed}')
        self.stdout.write(f'Successfully updated: {updated}')
        self.stdout.write(f'Failed: {failed}')
        self.stdout.write('=' * 80 + '\n')
