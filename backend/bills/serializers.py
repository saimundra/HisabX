from rest_framework import serializers
from .models import Bill, Category
from django.conf import settings
from ocr.utils.ocr_processor import process_bill_image
import logging

logger = logging.getLogger(__name__)

class CategorySerializer(serializers.ModelSerializer):
    bill_count = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_bill_count(self, obj):
        """Get the count of bills in this category"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.bill_set.filter(user=request.user).count()
        return 0
    
    def get_total_amount(self, obj):
        """Get the total amount in NPR for this category"""
        from django.db.models import Sum
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            total = obj.bill_set.filter(user=request.user).aggregate(
                total=Sum('amount_npr')
            )['total']
            return float(total) if total else 0.0
        return 0.0

class BillSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True, required=False)
    image_url = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    tags_list = serializers.ListField(source='get_tags_list', read_only=True)

    class Meta:
        model = Bill
        fields = [
            'id', 'image', 'image_url', 'invoice_number', 'vendor', 'amount', 'tax_amount', 
            'currency', 'exchange_rate', 'amount_npr', 'bill_date', 'category', 'category_name', 
            'category_color', 'is_auto_categorized', 'confidence_score',
            'transaction_type', 'account_type', 'is_debit',
            'ocr_text', 'line_items', 'created_at', 'updated_at', 'tags', 'tags_list',
            'notes', 'is_business_expense', 'is_reimbursable'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_auto_categorized', 'confidence_score', 
                           'transaction_type', 'account_type', 'is_debit', 'exchange_rate', 'amount_npr']

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def validate_image(self, value):
        max_size = getattr(settings, "MAX_UPLOAD_SIZE", 10 * 1024 * 1024)

        if value.size > max_size:
            raise serializers.ValidationError(f"File size must be less than {max_size / (1024 * 1024):.2f}MB.")

        allowed = getattr(settings, "ALLOWED_UPLOAD_TYPES", ["image/jpeg", "image/png", "image/webp", "application/pdf"])
        content_type = getattr(value, 'content_type', '')
        
        if content_type not in allowed:
            raise serializers.ValidationError(f"Unsupported file type: {content_type}. Allowed types: {', '.join(allowed)}")

        return value

    def create(self, validated_data):
        uploaded_image = validated_data.pop('image')
        user = self.context['request'].user

        logger.info(f"Creating Bill for user: {user.username}")
        logger.debug(f"Image: {uploaded_image.name}, Type: {uploaded_image.content_type}, Size: {uploaded_image.size}")

        # Remove user from validated_data if it exists to avoid duplicate key error
        validated_data.pop('user', None)

        instance = Bill.objects.create(
            user=user,
            image=uploaded_image,
            **validated_data
        )

        # Process OCR and extract data
        try:
            logger.info(f"Starting OCR processing for bill ID: {instance.id}")
            bill_data = process_bill_image(instance.image.path)
            logger.info(f"OCR completed. Extracted text length: {len(bill_data.get('ocr_text', ''))}")
            
            # Update instance with extracted data
            instance.ocr_text = bill_data.get('ocr_text', '')
            instance.invoice_number = bill_data.get('invoice_number')
            instance.vendor = bill_data.get('vendor')
            instance.amount = bill_data.get('amount')
            instance.tax_amount = bill_data.get('tax_amount')
            instance.bill_date = bill_data.get('bill_date')
            instance.line_items = bill_data.get('line_items', [])
            
            # Extract PAN/VAT/Tax ID number from OCR text
            import re
            extracted_pan_vat = None
            if instance.ocr_text:
                # Tax ID patterns for multiple countries
                pan_patterns = [
                    # Nepal
                    r'(?:PAN\s*(?:number|no\.?|#)?)[:\s]*([0-9]{9})',  # PAN: 9 digits
                    r'(?:VAT\s*(?:number|no\.?|#)?)[:\s]*([0-9]{13})',  # VAT: 13 digits
                    r'(?:PN|VN|TIN)[:\s#]*([0-9]{7,13})',  # Generic Nepal
                    
                    # India
                    r'(?:PAN)[:\s#]*([A-Z]{5}[0-9]{4}[A-Z])',  # PAN: ABCDE1234F
                    r'(?:GSTIN?)[:\s#]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9][A-Z][0-9])',  # GSTIN: 15 chars
                    
                    # Australia
                    r'(?:ABN)[:\s#]*([0-9]{11})',  # ABN: 11 digits
                    r'(?:ACN)[:\s#]*([0-9]{9})',  # ACN: 9 digits
                    
                    # USA
                    r'(?:SSN)[:\s#]*([0-9]{3}[\-]?[0-9]{2}[\-]?[0-9]{4})',  # SSN: 123-45-6789
                    r'(?:EIN)[:\s#]*([0-9]{2}[\-]?[0-9]{7})',  # EIN: 12-3456789
                    r'(?:ITIN)[:\s#]*([9][0-9]{2}[\-]?[7][0-9][\-]?[0-9]{4})',  # ITIN: 9XX-7X-XXXX
                    
                    # European Union
                    r'(?:VAT|Tax\s*ID)[:\s#]*(DE[0-9]{9})',  # Germany
                    r'(?:VAT|Tax\s*ID)[:\s#]*(FR[A-Z0-9]{2}[0-9]{9})',  # France
                    r'(?:VAT|Tax\s*ID)[:\s#]*(GB[0-9]{9})',  # UK
                    r'(?:VAT|Tax\s*ID)[:\s#]*(IT[0-9]{11})',  # Italy
                    r'(?:VAT|Tax\s*ID)[:\s#]*(ES[A-Z0-9][0-9]{7}[A-Z0-9])',  # Spain
                    r'(?:VAT|Tax\s*ID)[:\s#]*([A-Z]{2}[A-Z0-9]{8,12})',  # Generic EU VAT
                ]
                
                for pattern in pan_patterns:
                    match = re.search(pattern, instance.ocr_text.upper())
                    if match:
                        # Remove hyphens and spaces for consistent comparison
                        extracted_pan_vat = re.sub(r'[\s\-]', '', match.group(1))
                        logger.info(f"Extracted Tax ID from bill: {extracted_pan_vat}")
                        break
            
            # Check for duplicate invoice before proceeding
            # Multiple checks for duplicate detection
            is_duplicate = False
            duplicate = None
            duplicate_reason = None
            
            # Check 1: Same invoice number + Same vendor
            if instance.invoice_number and instance.vendor:
                vendor_normalized = instance.vendor.strip().lower()
                
                potential_duplicates = Bill.objects.filter(
                    user=user,
                    invoice_number__iexact=instance.invoice_number.strip(),
                    vendor__iexact=vendor_normalized
                ).exclude(id=instance.id)
                
                if potential_duplicates.exists():
                    is_duplicate = True
                    duplicate = potential_duplicates.first()
                    duplicate_reason = f"Invoice #{instance.invoice_number} from {instance.vendor}"
                    logger.warning(f"Duplicate bill detected for user {user.username}: {duplicate_reason}")
            
            # Check 2: Same invoice number + Same PAN/VAT (different vendor name but same business)
            if not is_duplicate and instance.invoice_number and extracted_pan_vat:
                # Find bills with the same PAN/VAT in OCR text
                potential_duplicates = Bill.objects.filter(
                    user=user,
                    invoice_number__iexact=instance.invoice_number.strip(),
                    ocr_text__icontains=extracted_pan_vat
                ).exclude(id=instance.id)
                
                if potential_duplicates.exists():
                    is_duplicate = True
                    duplicate = potential_duplicates.first()
                    duplicate_reason = f"Invoice #{instance.invoice_number} with PAN/VAT {extracted_pan_vat}"
                    logger.warning(f"Duplicate bill detected for user {user.username}: {duplicate_reason}")
            
            # Allow multiple bills from same PAN/VAT as long as invoice numbers are different
            # This handles the case where same business issues multiple bills
            
            # If duplicate found, reject the upload
            if is_duplicate and duplicate:
                # Store the image path before deleting instance
                image_to_delete = instance.image if instance.image else None
                
                # Delete the newly created instance first
                instance.delete()
                
                # Then delete the image file
                if image_to_delete:
                    image_to_delete.delete(save=False)
                
                raise serializers.ValidationError({
                    'error': 'Duplicate bill detected',
                    'message': f'This bill already exists: {duplicate_reason}',
                    'duplicate_bill_id': duplicate.id,
                })
            
            # Log if duplicate check was limited
            if instance.invoice_number and not instance.vendor:
                # Invoice number extracted but vendor not found
                logger.warning(
                    f"Invoice number '{instance.invoice_number}' extracted but vendor not identified. "
                    f"Limited duplicate check applied."
                )
            elif not instance.invoice_number and not instance.amount:
                # Neither invoice number nor amount available
                logger.info(
                    f"Incomplete bill data for duplicate check. Bill will be accepted."
                )
            
            # Detect currency from OCR text
            ocr_text = bill_data.get('ocr_text', '').lower()
            # Check for NPR first (more specific indicators)
            if 'npr' in ocr_text or 'nepali' in ocr_text or ('rs.' in ocr_text and 'ps.' in ocr_text) or 'chitwan' in ocr_text or 'kathmandu' in ocr_text:
                instance.currency = 'NPR'
            elif '₹' in ocr_text or 'inr' in ocr_text or 'gstin' in ocr_text or 'gst' in ocr_text:
                instance.currency = 'INR'
            elif 'rupee' in ocr_text or 'rs.' in ocr_text:
                # Generic rupee - default to INR unless other indicators
                instance.currency = 'INR'
            elif '$' in ocr_text or 'usd' in ocr_text:
                instance.currency = 'USD'
            elif '€' in ocr_text or 'eur' in ocr_text:
                instance.currency = 'EUR'
            elif '£' in ocr_text or 'gbp' in ocr_text:
                instance.currency = 'GBP'
            
            # Auto-categorize the bill
            from bills.categorization_service import BillCategorizationService
            categorization_service = BillCategorizationService()
            
            # Try categorization based on vendor and OCR text
            text_to_analyze = f"{instance.vendor or ''} {instance.ocr_text or ''}".strip()
            category, confidence = categorization_service.categorize_by_keywords(text_to_analyze, vendor=instance.vendor)
            
            if category and confidence > 0.3:  # Minimum confidence threshold
                instance.category = category
                instance.is_auto_categorized = True
                instance.confidence_score = confidence
                logger.info(f"Auto-categorized bill as '{category.name}' with confidence {confidence:.2f}")
            
            # Determine if this is user's company bill (income) or external vendor bill (expense)
            is_own_company = False
            match_reason = None
            
            # Method 1: Check if vendor name matches user's company name
            if instance.vendor and user.company_name:
                vendor_normalized = instance.vendor.strip().lower()
                company_normalized = user.company_name.strip().lower()
                
                # Skip if vendor contains common invoice recipient indicators
                # These phrases indicate this is who the invoice was issued TO, not issued BY
                recipient_indicators = [
                    'issued to', 'bill to', 'billed to', 'sold to', 
                    'customer', 'client', 'attention', 'attn'
                ]
                skip_matching = any(indicator in vendor_normalized for indicator in recipient_indicators)
                
                if not skip_matching:
                    # Remove common business suffixes for better matching
                    import re
                    business_suffixes = r'\s*(pvt\.?|ltd\.?|limited|private|inc\.?|llc|corp\.?|corporation|co\.?)\s*'
                    vendor_clean = re.sub(business_suffixes, '', vendor_normalized, flags=re.IGNORECASE).strip()
                    company_clean = re.sub(business_suffixes, '', company_normalized, flags=re.IGNORECASE).strip()
                    
                    # Require minimum length to avoid false positives
                    min_match_length = 5
                    
                    # Check for exact match or strong partial match
                    if len(company_clean) >= min_match_length:
                        if (vendor_normalized == company_normalized or 
                            vendor_clean == company_clean or
                            (vendor_normalized.startswith(company_normalized) and len(company_normalized) >= min_match_length) or
                            (company_normalized.startswith(vendor_normalized) and len(vendor_normalized) >= min_match_length)):
                            is_own_company = True
                            match_reason = f"vendor name '{instance.vendor}' matches company '{user.company_name}'"
                            logger.info(f"INCOME DETECTED: {match_reason}")
            
            # Method 2: Check if PAN/VAT number appears in OCR text (fallback when vendor not extracted)
            if not is_own_company and user.pan_vat_number and instance.ocr_text:
                # Normalize PAN/VAT number (remove spaces, hyphens, convert to uppercase)
                import re
                pan_vat_normalized = re.sub(r'[\s\-]', '', user.pan_vat_number.strip().upper())
                
                # Use word boundaries to prevent matching PAN/VAT inside account numbers or other digits
                # Look for PAN/VAT with context clues like labels (PAN:, VAT:, TIN:, etc.)
                pan_vat_patterns = [
                    # With explicit labels (most reliable)
                    rf'(?:PAN|VAT|TIN|TAX\s*ID|REGISTRATION)\s*(?:NO\.?|NUMBER|#)?\s*[:\-]?\s*{re.escape(pan_vat_normalized)}',
                    # Standalone with word boundaries (stricter - requires minimum 9 digits to avoid false positives)
                    rf'\b{re.escape(pan_vat_normalized)}\b' if len(pan_vat_normalized) >= 9 else None,
                ]
                
                # Remove None patterns and search
                pan_vat_patterns = [p for p in pan_vat_patterns if p]
                for pattern in pan_vat_patterns:
                    if re.search(pattern, instance.ocr_text.upper()):
                        is_own_company = True
                        match_reason = f"PAN/VAT '{user.pan_vat_number}' found in bill"
                        logger.info(f"INCOME DETECTED: PAN/VAT number '{user.pan_vat_number}' detected in OCR text - bill belongs to user's company")
                        break
            
            # Set transaction type based on ownership - THIS IS CRITICAL
            if is_own_company:
                # This is income - bill issued by user's own company
                instance.transaction_type = 'CREDIT'
                instance.account_type = 'REVENUE'
                instance.is_debit = False
                logger.info(f"✓ Bill identified as user's company invoice ({match_reason}) - marked as REVENUE (CREDIT)")
            else:
                # This is an expense - bill from external vendor
                instance.transaction_type = 'DEBIT'
                instance.account_type = 'EXPENSE'
                instance.is_debit = True
                if instance.vendor:
                    logger.info(f"Bill vendor '{instance.vendor}' is external - marked as EXPENSE (DEBIT)")
                else:
                    logger.info(f"Bill marked as EXPENSE (DEBIT) - no vendor/PAN match found")
            
            try:
                instance.save()
            except Exception as e:
                # Handle database constraint errors (duplicate detection)
                if 'UNIQUE constraint failed' in str(e) or 'duplicate key' in str(e).lower():
                    # Delete the uploaded image
                    if instance.image:
                        instance.image.delete()
                    
                    # Try to find the duplicate
                    try:
                        duplicate = Bill.objects.get(
                            user=user,
                            invoice_number__iexact=instance.invoice_number,
                            vendor__iexact=instance.vendor
                        )
                        raise serializers.ValidationError({
                            'error': 'Duplicate bill detected',
                            'message': 'This bill already exists. Duplicate bill detected.',
                            'duplicate_bill_id': duplicate.id,
                        })
                    except Bill.DoesNotExist:
                        raise serializers.ValidationError({
                            'error': 'Duplicate bill detected',
                            'message': 'This bill already exists. Duplicate bill detected.'
                        })
                else:
                    # Re-raise other exceptions
                    raise
            
        except serializers.ValidationError:
            # Re-raise validation errors (like duplicate detection)
            raise
        except Exception as e:
            logger.error(f"OCR processing failed for bill ID {instance.id}: {str(e)}")
            # Don't fail the entire upload if OCR fails
            instance.ocr_text = f"OCR Error: {str(e)}"
            instance.save()

        logger.info(f"Bill created successfully with ID: {instance.id}")
        return instance

    def update(self, instance, validated_data):
        """Update bill instance, handling optional image field"""
        logger.info(f"Updating Bill ID: {instance.id}")
        
        # Handle image update if provided
        if 'image' in validated_data:
            uploaded_image = validated_data.pop('image')
            # Delete old image if it exists
            if instance.image:
                instance.image.delete()
            instance.image = uploaded_image
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        logger.info(f"Bill ID {instance.id} updated successfully")
        return instance