from django.core.management.base import BaseCommand
from bills.categorization_service import BillCategorizationService
from bills.models import Bill
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Train ML categorization model on manually categorized bills'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-samples',
            type=int,
            default=10,
            help='Minimum number of bills per category'
        )

    def handle(self, *args, **options):
        min_samples = options['min_samples']
        
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Training ML Categorization Model'))
        self.stdout.write('=' * 80)
        
        # Check if we have enough training data
        manually_categorized = Bill.objects.filter(
            category__isnull=False,
            is_auto_categorized=False
        )
        
        count = manually_categorized.count()
        self.stdout.write(f'Found {count} manually categorized bills for training\n')
        
        if count < min_samples:
            self.stdout.write(
                self.style.ERROR(
                    f"Not enough training data. Need at least {min_samples} manually categorized bills. "
                    f"Currently have {count}."
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "\nTip: Manually categorize more bills in the admin panel or frontend, "
                    "ensuring is_auto_categorized is set to False for training data."
                )
            )
            return
        
        # Show category distribution
        self.stdout.write('Category distribution:')
        from django.db.models import Count
        categories = manually_categorized.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for cat in categories:
            self.stdout.write(f"  {cat['category__name']}: {cat['count']} bills")
        
        self.stdout.write('\n' + '-' * 80)
        self.stdout.write('Starting training...\n')
        
        # Train model
        service = BillCategorizationService(use_ml=True)
        
        success = service.train_ml_model()
        
        if success:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(self.style.SUCCESS('✓ Model trained successfully!'))
            self.stdout.write('=' * 80)
            
            # Show feature importance
            if service.ml_categorizer:
                self.stdout.write("\nTop 10 features for categorization:")
                features = service.ml_categorizer.get_feature_importance(top_n=10)
                if features:
                    for i, (feature, importance) in enumerate(features, 1):
                        self.stdout.write(f"  {i}. {feature}: {importance:.4f}")
            
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('Model is ready to use for bill categorization!')
            self.stdout.write('Use --use-ml flag with recategorize_bills command')
            self.stdout.write('=' * 80 + '\n')
        else:
            self.stdout.write(self.style.ERROR('\n✗ Model training failed!'))
            self.stdout.write('Check logs for details.\n')
