from django.core.management.base import BaseCommand
from django.db import models
from bills.models import Bill, Category
from bills.categorization_service import BillCategorizationService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re-categorize existing bills using updated vendor categories CSV data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recategorize all bills, including those already categorized',
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=0.0,
            help='Only recategorize bills with confidence below this threshold (default: 0.0 = all)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Only recategorize bills for a specific user ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of bills to process',
            default=None
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating the database',
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Starting Bill Re-categorization'))
        self.stdout.write('=' * 80)
        
        # Initialize categorization service
        service = BillCategorizationService()
        self.stdout.write(f'Loaded {len(service.vendor_mappings)} vendor mappings from CSV\n')

        # Get bills to process
        bills = Bill.objects.all()
        
        if options['user_id']:
            bills = bills.filter(user_id=options['user_id'])
            self.stdout.write(f'Filtering bills for user ID: {options["user_id"]}')
        
        if not options['force']:
            # Only process bills without category or with low confidence
            bills = bills.filter(
                models.Q(category__isnull=True) |
                models.Q(confidence_score__lt=options['min_confidence']) |
                models.Q(is_auto_categorized=False)
            )
            self.stdout.write(f'Processing bills without category or low confidence')
        else:
            self.stdout.write(f'Processing ALL bills (--force enabled)')
        
        total_count = bills.count()
        
        if options['limit']:
            bills = bills[:options['limit']]
            self.stdout.write(f'Limited to {options["limit"]} bills')
        
        self.stdout.write(f'\nTotal bills to process: {bills.count()}\n')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved\n'))

        # Statistics
        processed = 0
        categorized = 0
        unchanged = 0
        improved = 0
        failed = 0
        
        category_changes = {}

        for bill in bills:
            try:
                old_category = bill.category.name if bill.category else 'Uncategorized'
                old_confidence = bill.confidence_score or 0.0
                
                # Get category and confidence from vendor or text
                text_to_analyze = f"{bill.vendor or ''} {bill.ocr_text or ''}".strip()
                new_category, new_confidence = service.categorize_by_keywords(
                    text_to_analyze, 
                    vendor=bill.vendor
                )
                
                if new_category:
                    new_category_name = new_category.name
                    
                    # Determine if this is an improvement
                    is_change = False
                    is_improvement = False
                    
                    if old_category == 'Uncategorized':
                        is_change = True
                        is_improvement = True
                    elif old_category != new_category_name:
                        is_change = True
                        if new_confidence > old_confidence:
                            is_improvement = True
                    elif new_confidence > old_confidence + 0.05:  # At least 5% improvement
                        is_change = True
                        is_improvement = True
                    
                    if is_change:
                        change_key = f"{old_category} → {new_category_name}"
                        category_changes[change_key] = category_changes.get(change_key, 0) + 1
                        
                        if is_improvement:
                            status = self.style.SUCCESS('✓ IMPROVED')
                            improved += 1
                        else:
                            status = self.style.WARNING('⟳ CHANGED')
                        
                        self.stdout.write(
                            f'{status} Bill #{bill.id} | '
                            f'Vendor: {bill.vendor or "N/A":<25} | '
                            f'{old_category:<20} ({old_confidence:.2f}) → '
                            f'{new_category_name:<20} ({new_confidence:.2f})'
                        )
                        
                        # Update bill if not dry run
                        if not options['dry_run']:
                            bill.category = new_category
                            bill.confidence_score = new_confidence
                            bill.is_auto_categorized = True
                            bill.save(update_fields=['category', 'confidence_score', 'is_auto_categorized', 'updated_at'])
                        
                        categorized += 1
                    else:
                        unchanged += 1
                        if processed < 10:  # Show first 10 unchanged
                            self.stdout.write(
                                f'  - Bill #{bill.id} | '
                                f'Vendor: {bill.vendor or "N/A":<25} | '
                                f'Category: {old_category:<20} | No change needed'
                            )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Bill #{bill.id} | '
                            f'Vendor: {bill.vendor or "N/A":<25} | '
                            f'Could not determine category'
                        )
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
        self.stdout.write(self.style.SUCCESS('RE-CATEGORIZATION COMPLETE'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'Total bills processed: {processed}/{total_count}')
        self.stdout.write(f'Successfully categorized/updated: {categorized}')
        self.stdout.write(f'  - Improved: {improved}')
        self.stdout.write(f'  - Changed: {categorized - improved}')
        self.stdout.write(f'Unchanged: {unchanged}')
        self.stdout.write(f'Failed: {failed}')
        
        if category_changes:
            self.stdout.write('\n' + '-' * 80)
            self.stdout.write('Category Changes Summary:')
            self.stdout.write('-' * 80)
            for change, count in sorted(category_changes.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f'  {change}: {count} bills')
        
        if options['dry_run']:
            self.stdout.write('\n' + self.style.WARNING('DRY RUN - No changes were saved to the database'))
        
        self.stdout.write('=' * 80 + '\n')
