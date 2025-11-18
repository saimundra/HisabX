
from django.db import models
from django.contrib.auth.models import User
from accounts.models import CustomUser
import json

class Category(models.Model):
    CATEGORY_TYPES = [
        ('FOOD', 'Food & Dining'),
        ('TRANSPORT', 'Transportation'),
        ('UTILITIES', 'Utilities'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('HEALTHCARE', 'Healthcare'),
        ('SHOPPING', 'Shopping'),
        ('EDUCATION', 'Education'),
        ('BUSINESS', 'Business'),
        ('TRAVEL', 'Travel'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    keywords = models.TextField(help_text="Comma-separated keywords for auto-categorization")
    color = models.CharField(max_length=7, default="#808080")  # Hex color
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def get_keywords_list(self):
        return [keyword.strip().lower() for keyword in self.keywords.split(',') if keyword.strip()]

class Bill(models.Model):
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('INR', 'Indian Rupee'),
        ('NPR', 'Nepali Rupee'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bills')
    image = models.ImageField(upload_to='bills/%Y/%m/%d/')
    
    # Enhanced fields
    invoice_number = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text="Invoice/Bill number")
    vendor = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    bill_date = models.DateField(null=True, blank=True)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_auto_categorized = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)  # AI confidence
    
    # Original fields
    ocr_text = models.TextField(blank=True)
    line_items = models.JSONField(default=list, blank=True, help_text="List of items/goods in the bill")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Tags for custom labeling
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Additional metadata
    notes = models.TextField(blank=True)
    is_business_expense = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        # Unique constraint: Same invoice number from same vendor for same user = duplicate
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'invoice_number', 'vendor'],
                name='unique_invoice_per_vendor_per_user',
                condition=models.Q(invoice_number__isnull=False) & models.Q(vendor__isnull=False)
            )
        ]
        indexes = [
            models.Index(fields=['user', 'invoice_number', 'vendor']),
            models.Index(fields=['user', 'bill_date']),
        ]
    
    def __str__(self):
        return f"Bill - {self.vendor or 'Unknown'} - ${self.amount or 'N/A'}"
    
    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]