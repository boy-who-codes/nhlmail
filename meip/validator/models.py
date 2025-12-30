from django.db import models
from django.utils import timezone

class SMTPSender(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.email

class DisposableDomain(models.Model):
    domain = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.domain

class SystemConfig(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.key}: {self.value}"

class ValidationBatch(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    csv_file = models.FileField(upload_to='uploads/')
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ])
    total_emails = models.IntegerField(default=0)
    processed_emails = models.IntegerField(default=0)
    current_processing_email = models.CharField(max_length=255, blank=True, null=True, default='')

    def __str__(self):
        return f"Batch {self.id} - {self.created_at}"

class EmailResult(models.Model):
    batch = models.ForeignKey(ValidationBatch, on_delete=models.CASCADE, related_name='results', null=True, blank=True)
    email = models.EmailField()
    # Normalized email
    normalized_email = models.EmailField(blank=True, null=True)
    
    # Validation Fields
    syntax_valid = models.BooleanField(default=False)
    domain_valid = models.BooleanField(default=False)
    is_disposable = models.BooleanField(default=False)
    is_role_based = models.BooleanField(default=False)
    catch_all = models.CharField(max_length=20, default='No') # No, Possible
    domain_age_days = models.IntegerField(null=True, blank=True)
    provider = models.CharField(max_length=50, blank=True, null=True)
    smtp_check = models.CharField(max_length=20, default='Unknown') # Success, Fail, Unknown
    check_message = models.TextField(blank=True, null=True) # Detailed SMTP response
    has_anti_spam = models.BooleanField(default=False)
    has_spf = models.BooleanField(default=False)
    has_dmarc = models.BooleanField(default=False)
    spam_filter = models.CharField(max_length=50, blank=True, null=True) # e.g. Barracuda, Mimecast
    is_spammy = models.BooleanField(default=False)
    is_asian_region = models.BooleanField(default=False)
    firewall_info = models.CharField(max_length=100, blank=True, null=True)  # Firewall detection info
    bounce_history = models.BooleanField(default=False)
    
    rtpc_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20) # DELIVERABLE, RISKY, NOT DELIVERABLE
    recommendation = models.CharField(max_length=20) # SEND, DO NOT SEND
    reason = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} ({self.status})"
