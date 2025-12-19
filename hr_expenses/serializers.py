# hr_expenses/serializers.py
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import ExpenseCategory, ExpenseClaim, Receipt, ReimbursementHistory
from authentication.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for Expense Categories"""
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'category_type', 'category_type_display',
            'description', 'requires_receipt', 'max_amount',
            'approval_required', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReceiptSerializer(serializers.ModelSerializer):
    """Serializer for Receipt uploads"""
    uploaded_by_name = serializers.SerializerMethodField()
    verified_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Receipt
        fields = [
            'id', 'claim', 'file', 'file_url', 'file_name', 
            'file_size', 'file_type',
            'amount', 'receipt_date', 'vendor_name', 'receipt_number',
            'is_verified', 'verified_by', 'verified_by_name',
            'verified_at', 'verification_notes',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = [
            'uploaded_by', 'uploaded_at', 'file_size', 
            'file_type', 'file_name', 'is_verified',
            'verified_by', 'verified_at'
        ]
    
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None
    
    def get_verified_by_name(self, obj):
        return obj.verified_by.get_full_name() if obj.verified_by else None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class ReimbursementHistorySerializer(serializers.ModelSerializer):
    """Serializer for Reimbursement History"""
    action_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ReimbursementHistory
        fields = [
            'id', 'claim', 'previous_status', 'new_status',
            'action_by', 'action_by_name', 'action_timestamp',
            'notes', 'previous_amount', 'new_amount'
        ]
        read_only_fields = ['action_timestamp']
    
    def get_action_by_name(self, obj):
        return obj.action_by.get_full_name() if obj.action_by else None


class ExpenseClaimSerializer(serializers.ModelSerializer):
    """Full serializer for Expense Claims"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    reimbursed_by_name = serializers.SerializerMethodField()
    
    # Include related receipts
    receipts = ReceiptSerializer(many=True, read_only=True)
    
    # Computed fields
    total_receipts_amount = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    has_receipts = serializers.BooleanField(read_only=True)
    days_pending = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ExpenseClaim
        fields = [
            'id', 'claim_number', 'employee', 'employee_name', 
            'employee_id', 'employee_email',
            'category', 'category_name',
            'title', 'description', 'amount', 'currency', 'expense_date',
            'vendor_name', 'invoice_number', 'project_code',
            'priority', 'priority_display',
            'status', 'status_display', 'submitted_at',
            'reviewer', 'reviewer_name', 'reviewed_at', 'review_notes',
            'reimbursement_mode', 'reimbursement_date', 
            'reimbursement_reference', 'reimbursed_by', 'reimbursed_by_name',
            'receipts', 'total_receipts_amount', 'has_receipts', 'days_pending',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'claim_number', 'submitted_at', 'reviewed_at',
            'created_at', 'updated_at'
        ]
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id
    
    def get_employee_email(self, obj):
        return obj.employee.user.email
    
    def get_reviewer_name(self, obj):
        return obj.reviewer.get_full_name() if obj.reviewer else None
    
    def get_reimbursed_by_name(self, obj):
        return obj.reimbursed_by.get_full_name() if obj.reimbursed_by else None
    
    def validate(self, data):
        """Validate expense claim data"""
        # Check if category is active
        category = data.get('category')
        if category and not category.is_active:
            raise serializers.ValidationError({
                'category': 'This expense category is not active.'
            })
        
        # Check max amount limit
        amount = data.get('amount')
        if category and category.max_amount and amount:
            if amount > category.max_amount:
                raise serializers.ValidationError({
                    'amount': f'Amount exceeds category limit of {category.max_amount}'
                })
        
        # Validate expense date is not in future
        expense_date = data.get('expense_date')
        if expense_date and expense_date > timezone.now().date():
            raise serializers.ValidationError({
                'expense_date': 'Expense date cannot be in the future.'
            })
        
        return data


class ExpenseClaimListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing expense claims"""
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_pending = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ExpenseClaim
        fields = [
            'id', 'claim_number', 'employee', 'employee_name', 'employee_id',
            'category_name', 'title', 'amount', 'currency',
            'expense_date', 'status', 'status_display',
            'submitted_at', 'days_pending', 'created_at'
        ]
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()
    
    def get_employee_id(self, obj):
        return obj.employee.employee_id


class ExpenseClaimSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting expense claims"""
    claim_id = serializers.IntegerField()
    notes = serializers.CharField(required=False, allow_blank=True)


class ExpenseClaimApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting expense claims"""
    action = serializers.ChoiceField(choices=['APPROVE', 'REJECT'])
    review_notes = serializers.CharField(required=False, allow_blank=True)
    adjusted_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text="Adjusted amount if different from claimed"
    )


class ReimbursementProcessSerializer(serializers.Serializer):
    """Serializer for processing reimbursement"""
    claim_id = serializers.IntegerField(required=False)
    reimbursement_mode = serializers.ChoiceField(
        choices=[
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CHEQUE', 'Cheque'),
            ('CASH', 'Cash'),
            ('PAYROLL', 'Through Payroll'),
        ]
    )
    reimbursement_date = serializers.DateField(default=timezone.now().date())
    reimbursement_reference = serializers.CharField(max_length=100)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        """Ensure provided claim_id matches the target claim when supplied."""
        claim = self.context.get('claim')
        claim_id = attrs.get('claim_id')

        if claim_id and claim and claim_id != claim.id:
            raise serializers.ValidationError({
                'claim_id': 'Claim ID in payload does not match the URL resource.'
            })

        return attrs
