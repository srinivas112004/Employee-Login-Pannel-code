# hr_expenses/models.py
from django.db import models
from django.core.validators import MinValueValidator
from authentication.models import User
from hr_profile.models import EmployeeProfile


class ExpenseCategory(models.Model):
    """Expense categories for organization"""
    CATEGORY_CHOICES = [
        ('TRAVEL', 'Travel'),
        ('FOOD', 'Food & Meals'),
        ('ACCOMMODATION', 'Accommodation'),
        ('TRANSPORT', 'Local Transport'),
        ('OFFICE_SUPPLIES', 'Office Supplies'),
        ('TRAINING', 'Training & Development'),
        ('COMMUNICATION', 'Communication'),
        ('CLIENT_ENTERTAINMENT', 'Client Entertainment'),
        ('MEDICAL', 'Medical'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True, null=True)
    requires_receipt = models.BooleanField(default=True, help_text="Receipt mandatory for this category")
    max_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Maximum allowed amount per claim"
    )
    approval_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Expense Categories"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"


class ExpenseClaim(models.Model):
    """Employee expense claims"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('REIMBURSED', 'Reimbursed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    claim_number = models.CharField(max_length=20, unique=True, editable=False)
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='expense_claims')
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='claims')
    
    # Claim details
    title = models.CharField(max_length=200, help_text="Brief description of expense")
    description = models.TextField(help_text="Detailed description")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='INR')
    expense_date = models.DateField(help_text="Date when expense was incurred")
    
    # Additional info
    vendor_name = models.CharField(max_length=200, blank=True, null=True, help_text="Vendor/Merchant name")
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    project_code = models.CharField(max_length=50, blank=True, null=True, help_text="Project/Cost center code")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Approval workflow
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_claims',
        help_text="Manager/Approver"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, null=True, help_text="Reviewer comments")
    
    # Reimbursement details
    reimbursement_mode = models.CharField(
        max_length=50, 
        choices=[
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CHEQUE', 'Cheque'),
            ('CASH', 'Cash'),
            ('PAYROLL', 'Through Payroll'),
        ],
        null=True,
        blank=True
    )
    reimbursement_date = models.DateField(null=True, blank=True)
    reimbursement_reference = models.CharField(max_length=100, blank=True, null=True)
    reimbursed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reimbursed_claims'
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['claim_number']),
            models.Index(fields=['status', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"{self.claim_number} - {self.title} ({self.employee.employee_id})"
    
    def save(self, *args, **kwargs):
        if not self.claim_number:
            # Generate claim number: EXP-YYYYMM-####
            from django.utils import timezone
            now = timezone.now()
            prefix = f"EXP-{now.strftime('%Y%m')}"
            last_claim = ExpenseClaim.objects.filter(
                claim_number__startswith=prefix
            ).order_by('-claim_number').first()
            
            if last_claim:
                last_number = int(last_claim.claim_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.claim_number = f"{prefix}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def total_receipts_amount(self):
        """Calculate total amount from attached receipts"""
        return self.receipts.aggregate(
            total=models.Sum('amount')
        )['total'] or 0
    
    @property
    def has_receipts(self):
        """Check if claim has receipts attached"""
        return self.receipts.exists()
    
    @property
    def days_pending(self):
        """Calculate days since submission"""
        if self.submitted_at:
            from django.utils import timezone
            return (timezone.now() - self.submitted_at).days
        return None


class Receipt(models.Model):
    """Receipt/bill attachments for expense claims"""
    claim = models.ForeignKey(ExpenseClaim, on_delete=models.CASCADE, related_name='receipts')
    file = models.FileField(upload_to='expense_receipts/%Y/%m/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    file_type = models.CharField(max_length=50, help_text="MIME type")
    
    # Receipt details
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)]
    )
    receipt_date = models.DateField(null=True, blank=True)
    vendor_name = models.CharField(max_length=200, blank=True, null=True)
    receipt_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_receipts'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_receipts')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"Receipt for {self.claim.claim_number} - {self.file_name}"


class ReimbursementHistory(models.Model):
    """Track reimbursement history and changes"""
    claim = models.ForeignKey(ExpenseClaim, on_delete=models.CASCADE, related_name='history')
    
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20)
    
    action_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reimbursement_actions')
    action_timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    # Track amount changes (if any adjustments)
    previous_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Reimbursement Histories"
        ordering = ['-action_timestamp']
    
    def __str__(self):
        return f"{self.claim.claim_number} - {self.previous_status} → {self.new_status}"
