"""
Compliance and Policy Management Models
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PolicyCategory(models.Model):
    """Policy categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Policy Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Policy(models.Model):
    """Company policies that require employee acknowledgment"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    category = models.ForeignKey(PolicyCategory, on_delete=models.SET_NULL, null=True, related_name='policies')
    version = models.CharField(max_length=20, default='1.0')
    content = models.TextField(help_text="Full policy text in markdown or HTML")
    summary = models.TextField(blank=True, help_text="Brief summary for listings")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    is_mandatory = models.BooleanField(default=True, help_text="Must be acknowledged by all employees")
    applies_to_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="Empty list = all roles, or specify ['Admin', 'Employee', etc.]"
    )
    
    effective_date = models.DateField(help_text="Date when policy becomes effective")
    expiry_date = models.DateField(null=True, blank=True, help_text="Optional expiry date")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='policies_created')
    published_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='policies_published')
    published_at = models.DateTimeField(null=True, blank=True)
    
    requires_signature = models.BooleanField(default=False, help_text="Require digital signature")
    acknowledgment_deadline_days = models.IntegerField(default=7, help_text="Days to acknowledge after publication")
    
    attachment = models.FileField(upload_to='policies/%Y/%m/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Policies"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    @property
    def acknowledgment_count(self):
        """Count of users who acknowledged this policy"""
        return self.acknowledgments.filter(acknowledged=True).count()
    
    @property
    def pending_count(self):
        """Count of users who haven't acknowledged yet"""
        if self.status != 'published':
            return 0
        total_users = User.objects.filter(is_active=True).count()
        if self.applies_to_roles:
            total_users = User.objects.filter(is_active=True, role__in=self.applies_to_roles).count()
        return total_users - self.acknowledgment_count


class PolicyAcknowledgment(models.Model):
    """Track employee acknowledgments of policies"""
    
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='acknowledgments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='policy_acknowledgments')
    
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    signature = models.TextField(blank=True, help_text="Digital signature if required")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    comments = models.TextField(blank=True, help_text="Optional user comments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['policy', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        status = "Acknowledged" if self.acknowledged else "Pending"
        return f"{self.user.email} - {self.policy.title} ({status})"


class ComplianceReminder(models.Model):
    """Track automatic reminders sent to users"""
    
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compliance_reminders')
    
    sent_at = models.DateTimeField(auto_now_add=True)
    reminder_count = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Reminder to {self.user.email} for {self.policy.title}"
