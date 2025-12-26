from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True, help_text="Company/Business Name")
    pan_vat_number = models.CharField(max_length=50, blank=True, null=True, help_text="PAN/VAT Registration Number")
    business_type = models.CharField(max_length=100, blank=True, null=True, help_text="Type of Business")
    
    def __str__(self):
        return self.company_name or self.username