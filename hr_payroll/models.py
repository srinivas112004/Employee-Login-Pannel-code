# hr_payroll/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from authentication.models import User
from hr_profile.models import EmployeeProfile


class SalaryStructure(models.Model):
    """
    Salary structure template for different designations/levels
    """
    CURRENCY_CHOICES = [
        ('INR', 'Indian Rupee'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
    ]
    
    name = models.CharField(max_length=100, help_text="e.g., 'Junior Developer L1'")
    designation = models.CharField(max_length=100)
    level = models.CharField(max_length=50, blank=True, null=True)
    
    # Salary Components
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    hra = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="House Rent Allowance")
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    pf_employee = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, help_text="PF % (Employee)")
    pf_employer = models.DecimalField(max_digits=5, decimal_places=2, default=12.00, help_text="PF % (Employer)")
    esi_employee = models.DecimalField(max_digits=5, decimal_places=2, default=0.75, help_text="ESI % (Employee)")
    esi_employer = models.DecimalField(max_digits=5, decimal_places=2, default=3.25, help_text="ESI % (Employer)")
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2, default=200.00)
    
    # Tax
    tds = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="TDS % deduction")
    
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'salary_structures'
        verbose_name = 'Salary Structure'
        verbose_name_plural = 'Salary Structures'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.designation}"
    
    @property
    def gross_salary(self):
        """Total salary before deductions"""
        return (
            self.basic_salary + 
            self.hra + 
            self.transport_allowance + 
            self.medical_allowance + 
            self.special_allowance + 
            self.bonus
        )
    
    @property
    def total_deductions_percent(self):
        """Total deduction percentage"""
        return (
            self.pf_employee + 
            self.esi_employee + 
            self.tds
        )


class EmployeeSalary(models.Model):
    """
    Individual employee's assigned salary structure
    """
    employee = models.OneToOneField(
        EmployeeProfile, 
        on_delete=models.CASCADE, 
        related_name='salary'
    )
    salary_structure = models.ForeignKey(
        SalaryStructure, 
        on_delete=models.PROTECT,
        related_name='employee_salaries'
    )
    
    # Override fields if needed (custom salary for specific employee)
    custom_basic = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_hra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_transport = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_medical = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    custom_special = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_salaries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employee_salaries'
        verbose_name = 'Employee Salary'
        verbose_name_plural = 'Employee Salaries'
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.employee.user.email}"
    
    def get_component(self, component_name):
        """Get salary component value (custom or from structure)"""
        custom_value = getattr(self, f'custom_{component_name}', None)
        if custom_value is not None:
            return custom_value
        return getattr(self.salary_structure, component_name)
    
    @property
    def basic_salary(self):
        return self.custom_basic or self.salary_structure.basic_salary
    
    @property
    def gross_salary(self):
        return (
            self.basic_salary +
            (self.custom_hra or self.salary_structure.hra) +
            (self.custom_transport or self.salary_structure.transport_allowance) +
            (self.custom_medical or self.salary_structure.medical_allowance) +
            (self.custom_special or self.salary_structure.special_allowance) +
            self.salary_structure.bonus
        )


class Payslip(models.Model):
    """
    Generated monthly payslips for employees
    """
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('GENERATED', 'Generated'),
        ('APPROVED', 'Approved'),
        ('PAID', 'Paid'),
        ('ON_HOLD', 'On Hold'),
    ]
    
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='payslips'
    )
    employee_salary = models.ForeignKey(
        EmployeeSalary,
        on_delete=models.PROTECT,
        related_name='payslips'
    )
    
    # Period
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField(validators=[MinValueValidator(2020), MaxValueValidator(2100)])
    
    # Working days
    total_working_days = models.IntegerField(default=26)
    days_worked = models.DecimalField(max_digits=5, decimal_places=2, default=26)
    days_absent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Earnings
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2)
    hra = models.DecimalField(max_digits=12, decimal_places=2)
    transport_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    medical_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    special_allowance = models.DecimalField(max_digits=12, decimal_places=2)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    incentives = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Deductions
    pf_employee = models.DecimalField(max_digits=12, decimal_places=2)
    esi_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    professional_tax = models.DecimalField(max_digits=12, decimal_places=2)
    tds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Calculated fields
    gross_salary = models.DecimalField(max_digits=12, decimal_places=2)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2)
    net_salary = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='generated_payslips')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payslips')
    
    payment_date = models.DateField(null=True, blank=True)
    payment_mode = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., Bank Transfer, Cash")
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    remarks = models.TextField(blank=True, null=True)
    
    # PDF file
    pdf_file = models.FileField(upload_to='payslips/%Y/%m/', blank=True, null=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payslips'
        verbose_name = 'Payslip'
        verbose_name_plural = 'Payslips'
        ordering = ['-year', '-month', 'employee']
        unique_together = ['employee', 'month', 'year']
        indexes = [
            models.Index(fields=['employee', 'month', 'year']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.month}/{self.year}"
    
    @property
    def period_display(self):
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f"{months[self.month]} {self.year}"


class SalaryHistory(models.Model):
    """
    Track salary changes over time
    """
    CHANGE_TYPE_CHOICES = [
        ('INCREMENT', 'Increment'),
        ('PROMOTION', 'Promotion'),
        ('REVISION', 'Revision'),
        ('ADJUSTMENT', 'Adjustment'),
        ('BONUS', 'Bonus'),
    ]
    
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='salary_history'
    )
    
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    
    previous_salary = models.DecimalField(max_digits=12, decimal_places=2)
    new_salary = models.DecimalField(max_digits=12, decimal_places=2)
    percentage_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    effective_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_salary_changes'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_salary_changes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'salary_history'
        verbose_name = 'Salary History'
        verbose_name_plural = 'Salary Histories'
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.change_type} on {self.effective_date}"
    
    def save(self, *args, **kwargs):
        # Calculate percentage change
        if self.previous_salary and self.new_salary:
            self.percentage_change = (
                (self.new_salary - self.previous_salary) / self.previous_salary * 100
            )
        super().save(*args, **kwargs)


class Deduction(models.Model):
    """
    Additional deductions (loans, advances, penalties)
    """
    DEDUCTION_TYPE_CHOICES = [
        ('LOAN', 'Loan Repayment'),
        ('ADVANCE', 'Advance Deduction'),
        ('PENALTY', 'Penalty'),
        ('OTHER', 'Other'),
    ]
    
    employee = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.CASCADE,
        related_name='deductions'
    )
    
    deduction_type = models.CharField(max_length=20, choices=DEDUCTION_TYPE_CHOICES)
    description = models.CharField(max_length=255)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    installment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    start_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    start_year = models.IntegerField(validators=[MinValueValidator(2020)])
    
    end_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], null=True, blank=True)
    end_year = models.IntegerField(validators=[MinValueValidator(2020)], null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_deductions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deductions'
        verbose_name = 'Deduction'
        verbose_name_plural = 'Deductions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.employee_id} - {self.deduction_type}: {self.description}"
