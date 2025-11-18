from django.core.management.base import BaseCommand
from bills.models import Bill
from ocr.utils.ocr_processor import process_bill_image
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update line_items for existing bills by re-processing OCR'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all bills, even if they already have line items',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of bills to process',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Updating Line Items for Bills'))
        self.stdout.write('=' * 80)
        
        # Get bills to process
        if options['force']:
            bills = Bill.objects.all()
            self.stdout.write(f'Processing ALL {bills.count()} bills (--force enabled)')
        else:
            # Only process bills without line items
            bills = Bill.objects.filter(line_items=[])
            self.stdout.write(f'Processing {bills.count()} bills without line items')
        
        if options['limit']:
            bills = bills[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} bills\n')
        
        processed = 0
        updated = 0
        skipped = 0
        failed = 0
        
        for bill in bills:
            try:
                # Check if image file exists
                if not bill.image or not os.path.exists(bill.image.path):
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Bill #{bill.id} | No image file found | Skipped'
                        )
                    )
                    skipped += 1
                    continue
                
                # Re-process the bill image
                bill_data = process_bill_image(bill.image.path)
                line_items = bill_data.get('line_items', [])
                
                if line_items:
                    bill.line_items = line_items
                    bill.save(update_fields=['line_items'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Bill #{bill.id} | '
                            f'Vendor: {bill.vendor or "N/A":<25} | '
                            f'Extracted {len(line_items)} items'
                        )
                    )
                    updated += 1
                else:
                    self.stdout.write(
                        f'  Bill #{bill.id} | '
                        f'Vendor: {bill.vendor or "N/A":<25} | '
                        f'No line items found'
                    )
                    skipped += 1
                
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
        self.stdout.write(self.style.SUCCESS('UPDATE COMPLETE'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total bills processed: {processed}')
        self.stdout.write(f'Successfully updated: {updated}')
        self.stdout.write(f'Skipped (no items found): {skipped}')
        self.stdout.write(f'Failed: {failed}')
        self.stdout.write('=' * 80 + '\n')
