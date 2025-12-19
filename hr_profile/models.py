from django.db import models
from django.core.validators import RegexValidator
from authentication.models import User


class EmployeeProfile(models.Model):
    """Detailed employee profile with personal and professional information"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Single'),
        ('MARRIED', 'Married'),
        ('DIVORCED', 'Divorced'),
        ('WIDOWED', 'Widowed'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    # Relationships
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    reporting_manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='team_members'
    )
    
    # Basic Information
    employee_id = models.CharField(max_length=20, unique=True)
    designation = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    joining_date = models.DateField()
    
    # Personal Information
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    marital_status = models.CharField(max_length=10, choices=MARITAL_STATUS_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    
    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_primary = models.CharField(validators=[phone_regex], max_length=17)
    phone_secondary = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    email_personal = models.EmailField()
    
    # Address
    current_address = models.TextField()
    permanent_address = models.TextField(blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(validators=[phone_regex], max_length=17)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Bank Details
    bank_account_number = models.CharField(max_length=20, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_ifsc_code = models.CharField(max_length=11, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    
    # Profile Picture
    profile_picture = models.ImageField(upload_to='employee_documents/profile_pictures/', blank=True, null=True)
    
    # Onboarding Status
    onboarding_completed = models.BooleanField(default=False)
    onboarding_completed_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.email}"


class EmployeeDocument(models.Model):
    """Store employee documents like Aadhaar, PAN, etc."""
    
    DOCUMENT_TYPE_CHOICES = [
        ('AADHAAR', 'Aadhaar Card'),
        ('PAN', 'PAN Card'),
        ('PASSPORT', 'Passport'),
        ('DEGREE', 'Degree Certificate'),
        ('RESUME', 'Resume'),
        ('OFFER_LETTER', 'Offer Letter'),
        ('SALARY_SLIP', 'Salary Slip'),
        ('BANK_PROOF', 'Bank Proof'),
        ('OTHER', 'Other'),
    ]
    
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_file = models.FileField(upload_to='employee_documents/')
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Employee Document'
        verbose_name_plural = 'Employee Documents'
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.document_type}"


class OnboardingChecklist(models.Model):
    """Track onboarding tasks for new employees"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='onboarding_tasks')
    task_name = models.CharField(max_length=200)
    task_description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDING')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_onboarding_tasks'
    )
    
    # Completion
    completed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='completed_onboarding_tasks'
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Dates
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', '-created_at']
        verbose_name = 'Onboarding Checklist'
        verbose_name_plural = 'Onboarding Checklists'
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.task_name}"


class EmploymentHistory(models.Model):
    """Track previous employment history of employees"""
    
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='employment_history')
    company_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    job_description = models.TextField(blank=True, null=True)
    reason_for_leaving = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Employment History'
        verbose_name_plural = 'Employment Histories'
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.company_name}"
