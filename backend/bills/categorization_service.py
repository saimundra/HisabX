import csv
import os
import re
from django.conf import settings
from bills.models import Bill, Category
import logging

logger = logging.getLogger(__name__)

class BillCategorizationService:
    def __init__(self, use_ml=True):
        self.use_ml = use_ml
        self.load_vendor_mappings()
        
        # Initialize ML categorizer
        if self.use_ml:
            try:
                from bills.ml_categorization import MLBillCategorizer
                self.ml_categorizer = MLBillCategorizer()
            except Exception as e:
                logger.error(f"Error initializing ML categorizer: {e}")
                self.ml_categorizer = None
        else:
            self.ml_categorizer = None
    
    def load_vendor_mappings(self):
        """Load vendor-category mappings from CSV"""
        self.vendor_mappings = {}
        csv_path = os.path.join(settings.BASE_DIR, 'data', 'vendor_categories.csv')
        
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    vendor = row['vendor'].lower()
                    category = row['category']
                    confidence = float(row.get('confidence', 0.9))
                    self.vendor_mappings[vendor] = {
                        'category': category,
                        'confidence': confidence
                    }
    
    def categorize_by_keywords(self, text, vendor=None):
        """Categorize bill based on vendor CSV mapping and keyword matching"""
        if not text:
            return None, 0.0
        
        text_lower = text.lower()
        best_category = None
        best_score = 0.0
        
        # First, try exact vendor matching from CSV (highest priority)
        if vendor:
            vendor_lower = vendor.lower().strip()
            # Check if vendor exists in CSV mappings
            if vendor_lower in self.vendor_mappings:
                mapping = self.vendor_mappings[vendor_lower]
                category_name = mapping['category']
                confidence = mapping['confidence']
                
                # Find category by name
                try:
                    category = Category.objects.get(name=category_name)
                    logger.info(f"Vendor '{vendor}' matched in CSV to category '{category_name}' with {confidence:.2f} confidence")
                    return category, confidence
                except Category.DoesNotExist:
                    logger.warning(f"Category '{category_name}' from CSV not found in database")
            
            # Check if vendor contains any keywords from CSV
            for csv_vendor, mapping in self.vendor_mappings.items():
                if csv_vendor in vendor_lower or vendor_lower in csv_vendor:
                    category_name = mapping['category']
                    confidence = mapping['confidence'] * 0.9  # Slightly lower for partial match
                    
                    try:
                        category = Category.objects.get(name=category_name)
                        logger.info(f"Vendor '{vendor}' partially matched CSV vendor '{csv_vendor}' to category '{category_name}'")
                        return category, confidence
                    except Category.DoesNotExist:
                        pass
        
        # Fallback: Get all categories with keywords
        categories = Category.objects.exclude(keywords='')
        
        for category in categories:
            keywords = category.get_keywords_list()
            score = 0.0
            
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer keywords higher
                    weight = len(keyword) / 10.0 + 1.0
                    score += weight
            
            # Normalize score by number of keywords
            if keywords:
                score = score / len(keywords)
            
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category, min(best_score * 0.8, 0.95)  # Cap confidence at 95%
    
    def categorize_bill(self, bill):
        """
        Main categorization method using hybrid approach:
        1. CSV vendor mapping (highest priority)
        2. ML model prediction (if available)
        3. Keyword matching (fallback)
        """
        category = None
        confidence = 0.0
        method = None
        
        # Try CSV vendor mapping first
        text_to_analyze = f"{bill.vendor or ''} {bill.ocr_text or ''}".strip()
        csv_category, csv_confidence = self.categorize_by_keywords(text_to_analyze, vendor=bill.vendor)
        
        # If CSV gives high confidence, use it
        if csv_category and csv_confidence > 0.8:
            category = csv_category
            confidence = csv_confidence
            method = "csv_mapping"
            logger.info(f"Using CSV mapping for bill {bill.id}")
        
        # Try ML model if CSV confidence is low or no match
        elif self.use_ml and self.ml_categorizer and self.ml_categorizer.model:
            try:
                ml_category, ml_confidence = self.ml_categorizer.predict_category(bill)
                
                # Use ML if confidence is reasonable
                if ml_category and ml_confidence > 0.5:
                    # If both CSV and ML agree, boost confidence
                    if csv_category == ml_category:
                        confidence = max(csv_confidence, ml_confidence) * 1.1
                        confidence = min(confidence, 0.99)  # Cap at 99%
                        category = ml_category
                        method = "csv_ml_agreement"
                        logger.info(f"CSV and ML agree for bill {bill.id}")
                    # If ML has higher confidence, use ML
                    elif ml_confidence > csv_confidence:
                        category = ml_category
                        confidence = ml_confidence
                        method = "ml_model"
                        logger.info(f"Using ML prediction for bill {bill.id}")
                    # Otherwise use CSV
                    else:
                        category = csv_category
                        confidence = csv_confidence
                        method = "csv_mapping"
                # Fall back to CSV if ML is low confidence
                elif csv_category:
                    category = csv_category
                    confidence = csv_confidence
                    method = "csv_fallback"
            except Exception as e:
                logger.error(f"Error using ML categorizer: {e}")
                # Fallback to CSV
                if csv_category:
                    category = csv_category
                    confidence = csv_confidence
                    method = "csv_fallback"
        
        # Final fallback to CSV/keyword result
        elif csv_category:
            category = csv_category
            confidence = csv_confidence
            method = "keyword_fallback"
        
        # Update bill if we have a category with sufficient confidence
        if category and confidence > 0.3:  # Minimum confidence threshold
            bill.category = category
            bill.is_auto_categorized = True
            bill.confidence_score = confidence
            bill.save()
            logger.info(f"Categorized bill {bill.id} as '{category.name}' with confidence {confidence:.2f} using {method}")
        
        return bill

    def bulk_categorize(self, bills):
        """Categorize multiple bills at once"""
        results = []
        for bill in bills:
            result = self.categorize_bill(bill)
            results.append(result)
        return results

    def bulk_categorize_bills(self, user=None):
        """Categorize all uncategorized bills"""
        queryset = Bill.objects.filter(category__isnull=True)
        if user:
            queryset = queryset.filter(user=user)
        
        categorized_count = 0
        for bill in queryset:
            try:
                self.categorize_bill(bill)
                categorized_count += 1
                logger.info(f"Categorized bill {bill.id}: {bill.category}")
            except Exception as e:
                logger.error(f"Error categorizing bill {bill.id}: {e}")
        
        return categorized_count
    
    def train_ml_model(self):
        """Train or retrain the ML categorization model"""
        if not self.ml_categorizer:
            try:
                from bills.ml_categorization import MLBillCategorizer
                self.ml_categorizer = MLBillCategorizer()
            except Exception as e:
                logger.error(f"Error initializing ML categorizer: {e}")
                return False
        
        success = self.ml_categorizer.train_model()
        return success
        
        return categorized_count