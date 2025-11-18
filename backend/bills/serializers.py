from rest_framework import serializers
from .models import Bill, Category
from django.conf import settings
from ocr.utils.ocr_processor import process_bill_image
from ocr.utils.excel_handler import save_to_excel
import logging

logger = logging.getLogger(__name__)

class CategorySerializer(serializers.ModelSerializer):
    bill_count = serializers.SerializerMethodField()
    total_by_currency = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_bill_count(self, obj):
        """Get the count of bills in this category"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return obj.bill_set.filter(user=request.user).count()
        return 0
    
    def get_total_by_currency(self, obj):
        """Get the total amount grouped by currency"""
        from django.db.models import Sum
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Group bills by currency and sum amounts
            bills = obj.bill_set.filter(user=request.user).values('currency').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            # Return as a dictionary {currency: total}
            return {bill['currency']: float(bill['total']) for bill in bills if bill['currency'] and bill['total']}
        return {}

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
            'currency', 'bill_date', 'category', 'category_name', 
            'category_color', 'is_auto_categorized', 'confidence_score',
            'ocr_text', 'line_items', 'created_at', 'updated_at', 'tags', 'tags_list',
            'notes', 'is_business_expense', 'is_recurring'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_auto_categorized', 'confidence_score']

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
            
            # Check for duplicate invoice before proceeding
            # Primary check: Same invoice number + Same vendor + Same user
            is_duplicate = False
            duplicate = None
            
            if instance.invoice_number and instance.vendor:
                # Normalize vendor name for comparison (case-insensitive, strip whitespace)
                vendor_normalized = instance.vendor.strip().lower()
                
                # Find potential duplicates by invoice number + vendor
                potential_duplicates = Bill.objects.filter(
                    user=user,
                    invoice_number__iexact=instance.invoice_number.strip(),  # Case-insensitive
                    vendor__iexact=vendor_normalized  # Case-insensitive
                ).exclude(id=instance.id)
                
                if potential_duplicates.exists():
                    is_duplicate = True
                    duplicate = potential_duplicates.first()
                    logger.warning(
                        f"Duplicate bill detected for user {user.username}: "
                        f"Invoice #{instance.invoice_number} from {instance.vendor}"
                    )
            
            # Fallback check: Same amount + Same vendor + Same date (if invoice number not available)
            elif instance.amount and instance.vendor and instance.bill_date:
                vendor_normalized = instance.vendor.strip().lower()
                
                # Find potential duplicates by amount + vendor + date
                potential_duplicates = Bill.objects.filter(
                    user=user,
                    amount=instance.amount,
                    vendor__iexact=vendor_normalized,
                    bill_date=instance.bill_date
                ).exclude(id=instance.id)
                
                if potential_duplicates.exists():
                    is_duplicate = True
                    duplicate = potential_duplicates.first()
                    logger.warning(
                        f"Duplicate bill detected for user {user.username}: "
                        f"Same amount (${instance.amount}), vendor ({instance.vendor}), and date ({instance.bill_date})"
                    )
            
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
                    'message': 'This bill already exists. A bill with the same details was already uploaded.',
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
            
            # Save to Excel for record keeping
            if bill_data.get('ocr_text'):
                save_to_excel([{
                    "Bill ID": instance.id,
                    "Invoice Number": instance.invoice_number or "N/A",
                    "Vendor": instance.vendor or "Unknown",
                    "Amount": str(instance.amount) if instance.amount else "N/A",
                    "Category": instance.category.name if instance.category else "Uncategorized",
                    "Confidence": f"{instance.confidence_score:.2f}" if instance.confidence_score else "N/A",
                    "Text": bill_data['ocr_text']
                }])
            
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