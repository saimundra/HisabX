import csv
import os
import re
from django.conf import settings
from bills.models import Bill, Category
import logging

logger = logging.getLogger(__name__)

class BillCategorizationService:
    def __init__(self):
        self.load_vendor_mappings()
    
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
        """Main categorization method using vendor CSV and keyword matching"""
        # Try categorization with vendor name and OCR text
        text_to_analyze = f"{bill.vendor or ''} {bill.ocr_text or ''}".strip()
        category, confidence = self.categorize_by_keywords(text_to_analyze, vendor=bill.vendor)
        
        if category and confidence > 0.3:  # Minimum confidence threshold
            bill.category = category
            bill.is_auto_categorized = True
            bill.confidence_score = confidence
            bill.save()
            logger.info(f"Categorized bill {bill.id} as '{category.name}' with confidence {confidence:.2f}")
        
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