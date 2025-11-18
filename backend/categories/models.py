from django.db import models

class CategoryRule(models.Model):
    category = models.ForeignKey('bills.Category', on_delete=models.CASCADE, related_name='rules')
    vendor_pattern = models.CharField(max_length=255, blank=True)
    amount_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    keywords = models.TextField(help_text="Keywords that trigger this rule")
    priority = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-priority']
    
    def __str__(self):
        return f"Rule for {self.category.name}"

class UserCategoryPreference(models.Model):
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    vendor = models.CharField(max_length=255)
    preferred_category = models.ForeignKey('bills.Category', on_delete=models.CASCADE)
    confidence = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'vendor']
    
    def __str__(self):
        return f"{self.user.username} - {self.vendor} -> {self.preferred_category.name}"
    