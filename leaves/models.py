from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from datetime import date, timedelta


class LeaveType(models.Model):
    """
    Different types of leaves available (Casual, Sick, Earned, etc.)
    """
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    default_days = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Default number of days allocated per year"
    )
    description = models.TextField(blank=True)
    requires_document = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveBalance(models.Model):
    """
    Track leave balance for each user and leave type
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaves_balances'  # Changed to avoid conflict
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.CASCADE,
        related_name='balances'
    )
    year = models.IntegerField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    available_days = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        unique_together = ('user', 'leave_type', 'year')
        ordering = ['-year', 'leave_type']

    def __str__(self):
        return f"{self.user.email} - {self.leave_type.name} ({self.year})"

    def update_balance(self):
        """Calculate and update available days"""
        self.available_days = self.total_days - self.used_days
        self.save()


class Leave(models.Model):
    """
    Leave application model
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name='leaves'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Document attachment (optional)
    document = models.FileField(
        upload_to='leave_documents/',
        null=True,
        blank=True
    )
    
    # Multi-level Approval workflow
    applied_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leave_requests_received',
        help_text="Primary approver (usually direct manager)"
    )
    secondary_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secondary_leave_requests',
        help_text="Secondary approver (for multi-level approval)"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leaves_approved'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Approval levels
    approval_level = models.IntegerField(
        default=1,
        help_text="1=Manager, 2=Department Head, 3=HR"
    )
    current_approval_level = models.IntegerField(
        default=1,
        help_text="Current stage in approval hierarchy"
    )
    requires_multi_level = models.BooleanField(
        default=False,
        help_text="True if leave requires multi-level approval (e.g., > 5 days)"
    )
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    approval_notification_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.leave_type.name} ({self.start_date} to {self.end_date})"

    def calculate_leave_days(self):
        """
        Calculate total leave days (including start and end date)
        Excludes weekends (Saturday and Sunday)
        """
        if not self.start_date or not self.end_date:
            return 0
        
        total_days = 0
        current_date = self.start_date
        
        while current_date <= self.end_date:
            # 5 = Saturday, 6 = Sunday
            if current_date.weekday() < 5:
                total_days += 1
            current_date += timedelta(days=1)
        
        return total_days

    def save(self, *args, **kwargs):
        # Calculate total days if not set
        if not self.total_days:
            self.total_days = self.calculate_leave_days()
        
        # Determine if multi-level approval is needed
        if self.total_days > 5 or self.leave_type.code in ['ML', 'PL']:
            self.requires_multi_level = True
        
        super().save(*args, **kwargs)
    
    def get_next_approver(self):
        """
        Get the next approver based on current approval level
        """
        if self.current_approval_level == 1:
            return self.applied_to
        elif self.current_approval_level == 2:
            return self.secondary_approver
        return None
    
    def can_be_approved_by(self, user):
        """
        Check if the given user can approve this leave at current level
        """
        if self.status != 'pending':
            return False
        
        if self.current_approval_level == 1 and self.applied_to == user:
            return True
        elif self.current_approval_level == 2 and self.secondary_approver == user:
            return True
        
        # HR and Admin can approve at any level
        if user.role in ['admin', 'hr']:
            return True
        
        return False
    
    def advance_approval_level(self):
        """
        Move to the next approval level in multi-level approval
        """
        if self.requires_multi_level and self.current_approval_level < 2:
            self.current_approval_level += 1
            self.status = 'pending'  # Reset to pending for next level
            return True
        else:
            self.status = 'approved'
            return False
