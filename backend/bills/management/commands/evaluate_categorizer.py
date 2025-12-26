from django.core.management.base import BaseCommand
from bills.ml_categorization import MLBillCategorizer
from bills.models import Bill
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

class Command(BaseCommand):
    help = 'Evaluate ML categorization model performance'

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Evaluating ML Categorization Model'))
        self.stdout.write('=' * 80 + '\n')
        
        ml_categorizer = MLBillCategorizer()
        
        if not ml_categorizer.model:
            self.stdout.write(
                self.style.ERROR(
                    "No trained model found. Train model first using 'train_categorizer' command."
                )
            )
            return
        
        # Get test bills (manually categorized)
        test_bills = Bill.objects.filter(
            category__isnull=False,
            is_auto_categorized=False
        )
        
        if test_bills.count() == 0:
            self.stdout.write(
                self.style.ERROR("No manually categorized bills found for evaluation.")
            )
            return
        
        y_true = []
        y_pred = []
        y_confidence = []
        
        self.stdout.write(f"Evaluating on {test_bills.count()} bills...\n")
        
        correct = 0
        total = 0
        
        for bill in test_bills:
            true_category = bill.category.name
            predicted_category, confidence = ml_categorizer.predict_category(bill)
            
            if predicted_category:
                y_true.append(true_category)
                y_pred.append(predicted_category.name)
                y_confidence.append(confidence)
                
                total += 1
                if true_category == predicted_category.name:
                    correct += 1
        
        # Show results
        self.stdout.write("=" * 80)
        self.stdout.write("EVALUATION RESULTS")
        self.stdout.write("=" * 80 + "\n")
        
        accuracy = correct / total if total > 0 else 0
        self.stdout.write(f"Overall Accuracy: {accuracy:.2%} ({correct}/{total})\n")
        
        avg_confidence = np.mean(y_confidence) if y_confidence else 0
        self.stdout.write(f"Average Confidence: {avg_confidence:.2%}\n")
        
        self.stdout.write("\nClassification Report:")
        self.stdout.write("-" * 80)
        self.stdout.write(classification_report(y_true, y_pred))
        
        self.stdout.write("\nConfusion Matrix:")
        self.stdout.write("-" * 80)
        unique_labels = sorted(set(y_true))
        cm = confusion_matrix(y_true, y_pred, labels=unique_labels)
        
        # Print confusion matrix with labels
        self.stdout.write("\n" + " " * 20 + "Predicted")
        header = " " * 15
        for label in unique_labels:
            header += f"{label[:10]:>12}"
        self.stdout.write(header)
        
        for i, true_label in enumerate(unique_labels):
            row = f"{true_label[:15]:15}"
            for j in range(len(unique_labels)):
                row += f"{cm[i][j]:>12}"
            self.stdout.write(row)
        
        self.stdout.write("\n" + "=" * 80 + "\n")
