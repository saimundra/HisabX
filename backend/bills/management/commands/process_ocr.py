from django.core.management.base import BaseCommand
from django.db import models
from bills.models import Bill
from ocr.utils.ocr_processor import extract_text_from_image
from ocr.utils.excel_handler import save_to_excel
import os

class Command(BaseCommand):
    help = 'Process existing bills with OCR to extract text'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocess bills that already have extracted text',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of bills to process',
            default=None
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting OCR processing for existing bills...'))

        # Get bills that need processing
        if options['force']:
            bills = Bill.objects.all()
            self.stdout.write(f'Processing ALL {bills.count()} bills (--force enabled)')
        else:
            bills = Bill.objects.filter(
                models.Q(extracted_text__isnull=True) | 
                models.Q(extracted_text='')
            )
            self.stdout.write(f'Processing {bills.count()} bills without extracted text')

        if options['limit']:
            bills = bills[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} bills')

        processed = 0
        failed = 0
        skipped = 0

        for bill in bills:
            try:
                self.stdout.write(f'Processing Bill {bill.id}: {bill.original_name}')

                # Check if file exists
                if not os.path.exists(bill.file.path):
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  File not found: {bill.file.path}')
                    )
                    skipped += 1
                    continue

                # Extract text using OCR
                extracted_text = extract_text_from_image(bill.file.path)
                
                if extracted_text and extracted_text.strip():
                    # Update bill with extracted text
                    bill.extracted_text = extracted_text.strip()
                    bill.save()

                    # Save to Excel for record keeping
                    try:
                        save_to_excel([{
                            "Bill ID": bill.id,
                            "Filename": bill.original_name,
                            "Text": extracted_text,
                            "Date": bill.uploaded_at.strftime('%Y-%m-%d'),
                            "Owner": bill.owner.username
                        }])
                    except Exception as excel_error:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  Excel save failed: {excel_error}')
                        )

                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Extracted {len(extracted_text)} characters')
                    )
                    processed += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  No text extracted from image')
                    )
                    bill.extracted_text = "No text found"
                    bill.save()
                    skipped += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ OCR failed: {str(e)}')
                )
                bill.extracted_text = f"OCR Error: {str(e)}"
                bill.save()
                failed += 1

        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== OCR Processing Complete ==='))
        self.stdout.write(f'✅ Successfully processed: {processed}')
        self.stdout.write(f'⚠️  Skipped: {skipped}')
        self.stdout.write(f'❌ Failed: {failed}')
        self.stdout.write(f'📊 Total bills in database: {Bill.objects.count()}')
        
        bills_with_text = Bill.objects.filter(
            extracted_text__isnull=False
        ).exclude(extracted_text='').exclude(extracted_text='No text found')
        
        self.stdout.write(f'📝 Bills with extracted text: {bills_with_text.count()}')