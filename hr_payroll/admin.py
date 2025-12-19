# hr_payroll/admin.py
from django.contrib import admin
from .models import SalaryStructure, EmployeeSalary, Payslip, SalaryHistory, Deduction


@admin.register(SalaryStructure)
class SalaryStructureAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'designation', 'level', 'basic_salary',
        'gross_salary', 'currency', 'is_active', 'created_at'
    ]
    list_filter = ['designation', 'is_active', 'currency', 'created_at']
    search_fields = ['name', 'designation', 'level']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'designation', 'level', 'currency', 'is_active')
        }),
        ('Salary Components', {
            'fields': (
                'basic_salary', 'hra', 'transport_allowance',
                'medical_allowance', 'special_allowance', 'bonus'
            )
        }),
        ('Deduction Percentages', {
            'fields': (
                'pf_employee', 'pf_employer', 
                'esi_employee', 'esi_employer',
                'professional_tax', 'tds'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeSalary)
class EmployeeSalaryAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'salary_structure', 'gross_salary',
        'effective_from', 'effective_to', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'effective_from', 'created_at']
    search_fields = ['employee__employee_id', 'employee__user__email']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    autocomplete_fields = ['employee', 'salary_structure', 'created_by']
    
    fieldsets = (
        ('Assignment', {
            'fields': ('employee', 'salary_structure', 'effective_from', 'effective_to', 'is_active')
        }),
        ('Custom Overrides (Optional)', {
            'fields': (
                'custom_basic', 'custom_hra', 'custom_transport',
                'custom_medical', 'custom_special'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'month', 'year', 'gross_salary',
        'net_salary', 'status', 'payment_date', 'generated_at'
    ]
    list_filter = ['status', 'month', 'year', 'generated_at', 'payment_date']
    search_fields = ['employee__employee_id', 'employee__user__email']
    readonly_fields = ['generated_at', 'updated_at', 'generated_by', 'approved_at']
    autocomplete_fields = ['employee', 'employee_salary', 'generated_by', 'approved_by']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'employee_salary', 'month', 'year')
        }),
        ('Working Days', {
            'fields': ('total_working_days', 'days_worked', 'days_absent')
        }),
        ('Earnings', {
            'fields': (
                'basic_salary', 'hra', 'transport_allowance',
                'medical_allowance', 'special_allowance', 'bonus',
                'overtime_pay', 'incentives', 'gross_salary'
            )
        }),
        ('Deductions', {
            'fields': (
                'pf_employee', 'esi_employee', 'professional_tax',
                'tds', 'loan_deduction', 'other_deductions', 'total_deductions'
            )
        }),
        ('Net Salary & Status', {
            'fields': ('net_salary', 'status', 'remarks')
        }),
        ('Payment Details', {
            'fields': ('payment_date', 'payment_mode', 'payment_reference', 'pdf_file')
        }),
        ('Audit Trail', {
            'fields': (
                'generated_by', 'generated_at',
                'approved_by', 'approved_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(SalaryHistory)
class SalaryHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'change_type', 'previous_salary',
        'new_salary', 'percentage_change', 'effective_date', 'approved_by'
    ]
    list_filter = ['change_type', 'effective_date', 'created_at']
    search_fields = ['employee__employee_id', 'employee__user__email']
    readonly_fields = ['percentage_change', 'created_at', 'created_by']
    autocomplete_fields = ['employee', 'approved_by', 'created_by']
    date_hierarchy = 'effective_date'
    
    fieldsets = (
        ('Employee & Change Details', {
            'fields': ('employee', 'change_type', 'effective_date')
        }),
        ('Salary Change', {
            'fields': ('previous_salary', 'new_salary', 'percentage_change', 'reason')
        }),
        ('Approval', {
            'fields': ('approved_by', 'created_by', 'created_at')
        }),
    )


@admin.register(Deduction)
class DeductionAdmin(admin.ModelAdmin):
    list_display = [
        'employee', 'deduction_type', 'description',
        'total_amount', 'remaining_amount', 'is_active',
        'is_completed', 'start_month', 'start_year'
    ]
    list_filter = ['deduction_type', 'is_active', 'is_completed', 'start_year']
    search_fields = ['employee__employee_id', 'employee__user__email', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    autocomplete_fields = ['employee', 'created_by']
    
    fieldsets = (
        ('Employee & Type', {
            'fields': ('employee', 'deduction_type', 'description')
        }),
        ('Amount Details', {
            'fields': ('total_amount', 'installment_amount', 'remaining_amount')
        }),
        ('Period', {
            'fields': (
                'start_month', 'start_year',
                'end_month', 'end_year'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'is_completed')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
