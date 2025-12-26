
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
    
    TRANSACTION_TYPE_CHOICES = [
        ('DEBIT', 'Debit (Expense/Asset Purchase)'),
        ('CREDIT', 'Credit (Income/Revenue)'),
    ]
    
    ACCOUNT_TYPE_CHOICES = [
        ('EXPENSE', 'Expense'),
        ('REVENUE', 'Revenue'),
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='bills')
    image = models.ImageField(upload_to='bills/%Y/%m/%d/')
    
    # Enhanced fields
    invoice_number = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text="Invoice/Bill number")
    vendor = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NPR')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000, help_text="Exchange rate to NPR at bill date")
    amount_npr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Amount converted to NPR")
    bill_date = models.DateField(null=True, blank=True)
    
    # Nepali Date (Bikram Sambat) Support
    bill_date_bs = models.CharField(max_length=10, blank=True, null=True, help_text='Bill date in Bikram Sambat (BS) format YYYY-MM-DD')
    use_bs_date = models.BooleanField(default=False, help_text='Whether to use BS date for display')
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    is_auto_categorized = models.BooleanField(default=False)
    confidence_score = models.FloatField(null=True, blank=True)  # AI confidence
    
    # Accounting Fields
    transaction_type = models.CharField(
        max_length=10, 
        choices=TRANSACTION_TYPE_CHOICES, 
        default='DEBIT',
        help_text="Debit (expense) or Credit (income)"
    )
    account_type = models.CharField(
        max_length=15,
        choices=ACCOUNT_TYPE_CHOICES,
        default='EXPENSE',
        help_text="Account classification for financial statements"
    )
    is_debit = models.BooleanField(default=True, help_text="True if expense (debit), False if income (credit)")
    
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
    is_reimbursable = models.BooleanField(default=False)
    
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
    
    def get_exchange_rate(self, currency, date=None):
        """Get exchange rate for currency to NPR"""
        from decimal import Decimal
        # Approximate exchange rates to NPR (as of 2025)
        # In production, use a real-time API like exchangerate-api.com
        exchange_rates = {
            'NPR': Decimal('1.0000'),
            'USD': Decimal('132.50'),  # 1 USD = 132.50 NPR
            'EUR': Decimal('145.00'),  # 1 EUR = 145.00 NPR
            'GBP': Decimal('168.00'),  # 1 GBP = 168.00 NPR
            'CAD': Decimal('95.00'),   # 1 CAD = 95.00 NPR
            'AUD': Decimal('85.00'),   # 1 AUD = 85.00 NPR
            'INR': Decimal('1.60'),    # 1 INR = 1.60 NPR
        }
        return exchange_rates.get(currency, Decimal('1.0000'))
    
    def save(self, *args, **kwargs):
        """Auto-classify transaction and convert currency to NPR"""
        # Convert to NPR if currency is different
        if self.amount and self.currency:
            self.exchange_rate = self.get_exchange_rate(self.currency, self.bill_date)
            self.amount_npr = self.amount * self.exchange_rate
        
        # Only auto-classify if transaction_type is not already set (for backward compatibility)
        # If transaction_type is already set (e.g., by serializer for income detection), preserve it
        if self.category and not self.transaction_type:
            # Map category type to account type
            category_to_account = {
                'FOOD': 'EXPENSE',
                'TRANSPORT': 'EXPENSE',
                'UTILITIES': 'EXPENSE',
                'ENTERTAINMENT': 'EXPENSE',
                'HEALTHCARE': 'EXPENSE',
                'SHOPPING': 'EXPENSE',
                'EDUCATION': 'EXPENSE',
                'BUSINESS': 'EXPENSE',
                'TRAVEL': 'EXPENSE',
                'OTHER': 'EXPENSE',
            }
            self.account_type = category_to_account.get(self.category.type, 'EXPENSE')
            self.is_debit = True  # Most bills are expenses (debits)
            self.transaction_type = 'DEBIT'
        super().save(*args, **kwargs)


class ChartOfAccounts(models.Model):
    """Chart of Accounts for double-entry bookkeeping"""
    ACCOUNT_CATEGORIES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('EQUITY', 'Equity'),
        ('REVENUE', 'Revenue'),
        ('EXPENSE', 'Expense'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='accounts')
    account_code = models.CharField(max_length=20, help_text="Account number (e.g., 1000, 5001)")
    account_name = models.CharField(max_length=200)
    account_category = models.CharField(max_length=15, choices=ACCOUNT_CATEGORIES)
    parent_account = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_accounts')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Chart of Accounts"
        unique_together = ['user', 'account_code']
        ordering = ['account_code']
    
    def __str__(self):
        return f"{self.account_code} - {self.account_name}"


class FinancialPeriod(models.Model):
    """Track financial periods for reporting"""
    PERIOD_TYPES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='financial_periods')
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
        unique_together = ['user', 'period_type', 'start_date']
    
    def __str__(self):
        return f"{self.get_period_type_display()} - {self.start_date} to {self.end_date}"


class JournalEntry(models.Model):
    """Double-entry journal entries"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='journal_entries')
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, null=True, blank=True, related_name='journal_entries')
    entry_date = models.DateField()
    description = models.TextField()
    reference_number = models.CharField(max_length=50, blank=True)
    financial_period = models.ForeignKey(FinancialPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Journal Entries"
        ordering = ['-entry_date']
    
    def __str__(self):
        return f"Entry {self.id} - {self.entry_date} - {self.description[:50]}"


class JournalEntryLine(models.Model):
    """Individual debit/credit lines in a journal entry"""
    ENTRY_TYPE_CHOICES = [
        ('DEBIT', 'Debit'),
        ('CREDIT', 'Credit'),
    ]
    
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.PROTECT, related_name='journal_lines')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['entry_type']  # Debits first, then credits
    
    def __str__(self):
        return f"{self.entry_type} - {self.account.account_name} - {self.amount}"