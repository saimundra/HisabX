from django.db import models
from django.contrib.auth import get_user_model
from bills.models import Bill, Category

User = get_user_model()

class ReportTemplate(models.Model):
    REPORT_TYPES = [
        ('MONTHLY', 'Monthly Report'),
        ('YEARLY', 'Yearly Report'),
        ('CATEGORY', 'Category Report'),
        ('VENDOR', 'Vendor Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class AuditReport(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'), 
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    EXPORT_FORMATS = [
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
        ('CSV', 'CSV'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Report parameters
    start_date = models.DateField()
    end_date = models.DateField()
    categories = models.ManyToManyField(Category, blank=True)
    vendors = models.TextField(blank=True, help_text="Comma-separated vendor names")
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Report metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMATS, default='PDF')
    file_path = models.CharField(max_length=500, blank=True)
    
    # Statistics
    total_bills = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

class ReportData(models.Model):
    """Stores processed data for reports"""
    report = models.ForeignKey(AuditReport, on_delete=models.CASCADE, related_name='data')
    category_name = models.CharField(max_length=100)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_count = models.IntegerField()
    percentage = models.FloatField()
    
    class Meta:
        ordering = ['-total_amount']
