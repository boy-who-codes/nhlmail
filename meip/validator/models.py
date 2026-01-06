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

class SpamTrap(models.Model):
    email = models.EmailField(unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

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

    @property
    def status_class(self):
        if self.status == 'DELIVERABLE':
            return "bg-green-500/10 text-green-500 border border-green-500/20 print:bg-green-100 print:text-green-800 print:border-green-300"
        elif self.status == 'RISKY':
            return "bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 print:bg-yellow-100 print:text-yellow-800 print:border-yellow-300"
        else:
            return "bg-red-500/10 text-red-500 border border-red-500/20 print:bg-red-100 print:text-red-800 print:border-red-300"

    @property
    def smtp_class(self):
        return "text-green-500" if self.smtp_check == 'Success' else "text-red-400"

    @property
    def catch_all_class(self):
        return "text-yellow-500" if self.catch_all == 'Yes' else "text-white"
        
    @property
    def warning_class(self):
        # Generic class for bad/good boolean states (Spammy, Disposable)
        return "text-red-500 font-bold"

    @property
    def success_class(self):
        return "text-green-500"

    @property
    def role_class(self):
        return "text-yellow-500" if self.is_role_based else "text-green-500"

    @property
    def spammy_class(self):
        return "text-red-500 font-bold" if self.is_spammy else "text-green-500"

    @property
    def disposable_class(self):
        return "text-red-500 font-bold" if self.is_disposable else "text-green-500"

    @property
    def auth_pass_class(self):
        return "bg-green-500/20 text-green-500"
    
    @property
    def auth_fail_class(self):
        return "bg-red-500/20 text-red-500"

    @property
    def spf_class(self):
        return self.auth_pass_class if self.has_spf else self.auth_fail_class

    @property
    def dmarc_class(self):
        return self.auth_pass_class if self.has_dmarc else self.auth_fail_class

    @property
    def domain_age_display(self):
        return f"{self.domain_age_days} days" if self.domain_age_days else "Unknown"


    def __str__(self):
        return f"{self.email} ({self.status})"
