import csv
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def add_company_to_vendor_csv(company_name, business_type):
    """
    Add user's company name to vendor_categories.csv for auto-categorization
    """
    if not company_name:
        return False
    
    csv_path = os.path.join(settings.BASE_DIR, 'data', 'vendor_categories.csv')
    
    # Map business_type to category
    business_type_to_category = {
        'Sole Proprietorship': 'Business',
        'Partnership': 'Business',
        'Private Limited Company': 'Business',
        'Public Limited Company': 'Business',
        'NGO/INGO': 'Other',
        'Cooperative': 'Business',
        'Government Entity': 'Business',
        'Other': 'Business',
    }
    
    category = business_type_to_category.get(business_type, 'Business')
    company_lower = company_name.strip().lower()
    
    try:
        # Check if company already exists in CSV
        existing_vendors = set()
        if os.path.exists(csv_path):
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_vendors.add(row['vendor'].lower())
        
        # If company doesn't exist, add it
        if company_lower not in existing_vendors:
            with open(csv_path, 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([company_lower, category, '0.95'])
            
            logger.info(f"Added company '{company_name}' to vendor_categories.csv with category '{category}'")
            return True
        else:
            logger.info(f"Company '{company_name}' already exists in vendor_categories.csv")
            return False
            
    except Exception as e:
        logger.error(f"Error adding company to CSV: {e}")
        return False
