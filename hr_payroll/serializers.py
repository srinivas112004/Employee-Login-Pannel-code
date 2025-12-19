# hr_payroll/serializers.py
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import SalaryStructure, EmployeeSalary, Payslip, SalaryHistory, Deduction
from hr_profile.models import EmployeeProfile
from authentication.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class SalaryStructureSerializer(serializers.ModelSerializer):
    """Serializer for Salary Structure templates"""
    gross_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_deductions_percent = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalaryStructure
        fields = [
            'id', 'name', 'designation', 'level',
            'basic_salary', 'hra', 'transport_allowance', 
            'medical_allowance', 'special_allowance', 'bonus',
            'pf_employee', 'pf_employer', 'esi_employee', 'esi_employer',
            'professional_tax', 'tds', 'currency', 'is_active',
            'gross_salary', 'total_deductions_percent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate salary components"""
        basic_salary = data.get('basic_salary')

        # When performing partial updates, fall back to the existing value
        if basic_salary is None and self.instance is not None:
            basic_salary = self.instance.basic_salary

        if basic_salary is None or basic_salary <= 0:
            raise serializers.ValidationError({'basic_salary': 'Basic salary must be greater than 0'})
        
        return data


class EmployeeSalarySerializer(serializers.ModelSerializer):
    """Serializer for Employee-specific salary assignments"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    salary_structure_name = serializers.CharField(source='salary_structure.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    gross_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    basic_salary = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = EmployeeSalary
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'salary_structure', 'salary_structure_name',
            'custom_basic', 'custom_hra', 'custom_transport',
            'custom_medical', 'custom_special',
            'basic_salary', 'gross_salary',
            'effective_from', 'effective_to', 'is_active',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_created_by_name(self, obj):
        return obj.created_by.email if obj.created_by else None
    
    def validate(self, data):
        """Validate effective dates"""
        if data.get('effective_to') and data.get('effective_from'):
            if data['effective_to'] < data['effective_from']:
                raise serializers.ValidationError({
                    'effective_to': 'End date must be after start date'
                })
        
        return data


class PayslipSerializer(serializers.ModelSerializer):
    """Serializer for Payslips"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    generated_by_name = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    period_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'employee_name', 'employee_id', 'employee_email',
            'employee_salary', 'month', 'year', 'period_display',
            'total_working_days', 'days_worked', 'days_absent',
            'basic_salary', 'hra', 'transport_allowance', 
            'medical_allowance', 'special_allowance', 'bonus',
            'overtime_pay', 'incentives',
            'pf_employee', 'esi_employee', 'professional_tax', 
            'tds', 'loan_deduction', 'other_deductions',
            'gross_salary', 'total_deductions', 'net_salary',
            'status', 'generated_by', 'generated_by_name',
            'approved_by', 'approved_by_name',
            'payment_date', 'payment_mode', 'payment_reference',
            'remarks', 'pdf_file',
            'generated_at', 'approved_at', 'updated_at'
        ]
        read_only_fields = [
            'generated_at', 'updated_at', 'generated_by', 
            'approved_at', 'gross_salary', 'total_deductions', 'net_salary'
        ]
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_employee_email(self, obj):
        return obj.employee.user.email
    
    def get_generated_by_name(self, obj):
        return obj.generated_by.email if obj.generated_by else None
    
    def get_approved_by_name(self, obj):
        return obj.approved_by.email if obj.approved_by else None
    
    def validate(self, data):
        """Validate payslip data"""
        if data.get('days_worked', 0) > data.get('total_working_days', 26):
            raise serializers.ValidationError({
                'days_worked': 'Days worked cannot exceed total working days'
            })
        
        if data.get('month'):
            if data['month'] < 1 or data['month'] > 12:
                raise serializers.ValidationError({
                    'month': 'Month must be between 1 and 12'
                })
        
        return data


class PayslipListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing payslips"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    period_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = Payslip
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'month', 'year', 'period_display',
            'gross_salary', 'total_deductions', 'net_salary',
            'status', 'payment_date', 'generated_at'
        ]
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id


class SalaryHistorySerializer(serializers.ModelSerializer):
    """Serializer for Salary History tracking"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SalaryHistory
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'change_type', 'previous_salary', 'new_salary',
            'percentage_change', 'effective_date', 'reason',
            'approved_by', 'approved_by_name',
            'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['created_at', 'created_by', 'percentage_change']
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_approved_by_name(self, obj):
        return obj.approved_by.email if obj.approved_by else None
    
    def get_created_by_name(self, obj):
        return obj.created_by.email if obj.created_by else None


class DeductionSerializer(serializers.ModelSerializer):
    """Serializer for additional deductions"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Deduction
        fields = [
            'id', 'employee', 'employee_name', 'employee_id',
            'deduction_type', 'description',
            'total_amount', 'installment_amount', 'remaining_amount',
            'start_month', 'start_year', 'end_month', 'end_year',
            'is_active', 'is_completed',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'is_completed']
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_created_by_name(self, obj):
        return obj.created_by.email if obj.created_by else None
    
    def validate(self, data):
        """Validate deduction data"""
        total_amount = data.get('total_amount')
        installment_amount = data.get('installment_amount')
        remaining_amount = data.get('remaining_amount')

        if self.instance is not None:
            if total_amount is None:
                total_amount = self.instance.total_amount
            if installment_amount is None:
                installment_amount = self.instance.installment_amount
            if remaining_amount is None:
                remaining_amount = self.instance.remaining_amount

        if total_amount is None:
            raise serializers.ValidationError({
                'total_amount': 'Total amount is required.'
            })

        if installment_amount is not None and installment_amount > total_amount:
            raise serializers.ValidationError({
                'installment_amount': 'Installment amount cannot exceed total amount'
            })

        if remaining_amount is not None and remaining_amount > total_amount:
            raise serializers.ValidationError({
                'remaining_amount': 'Remaining amount cannot exceed total amount'
            })
        
        return data


class PayrollGenerationSerializer(serializers.Serializer):
    """Serializer for bulk payroll generation"""
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2020, max_value=2100)
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of employee IDs. If empty, generates for all active employees"
    )
    total_working_days = serializers.IntegerField(default=26, min_value=1, max_value=31)
    
    def validate(self, data):
        """Validate payroll generation request"""
        # Check if payroll already exists for this period
        month = data['month']
        year = data['year']
        
        if data.get('employee_ids'):
            existing = Payslip.objects.filter(
                month=month,
                year=year,
                employee_id__in=data['employee_ids']
            ).values_list('employee__employee_id', flat=True)
            
            if existing:
                raise serializers.ValidationError({
                    'employee_ids': f'Payslips already exist for: {", ".join(existing)}'
                })
        
        return data
