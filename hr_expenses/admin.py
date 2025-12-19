# hr_expenses/admin.py
from django.contrib import admin
from .models import ExpenseCategory, ExpenseClaim, Receipt, ReimbursementHistory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'max_amount', 'requires_receipt', 'approval_required', 'is_active']
    list_filter = ['category_type', 'requires_receipt', 'approval_required', 'is_active']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category_type', 'description')
        }),
        ('Settings', {
            'fields': ('max_amount', 'requires_receipt', 'approval_required', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExpenseClaim)
class ExpenseClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_number', 'employee', 'category', 'amount', 'status', 'priority', 'expense_date', 'submitted_at']
    list_filter = ['status', 'priority', 'category', 'reimbursement_mode', 'submitted_at', 'expense_date']
    search_fields = ['claim_number', 'employee__employee_id', 'employee__user__username', 'description']
    readonly_fields = ['claim_number', 'submitted_at', 'reviewed_at', 'reimbursement_date', 'created_at', 'updated_at']
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        ('Claim Information', {
            'fields': ('claim_number', 'employee', 'category', 'amount', 'expense_date', 'priority')
        }),
        ('Description & Details', {
            'fields': ('description', 'purpose', 'project_code', 'location')
        }),
        ('Status & Workflow', {
            'fields': ('status', 'submitted_at', 'reviewer', 'reviewed_at', 'review_notes')
        }),
        ('Reimbursement', {
            'fields': ('reimbursement_mode', 'reimbursement_date', 'reimbursement_reference', 'reimbursed_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['employee', 'category']
        return self.readonly_fields


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ['claim', 'file_name', 'amount', 'receipt_date', 'uploaded_by', 'is_verified', 'uploaded_at']
    list_filter = ['is_verified', 'receipt_date', 'uploaded_at']
    search_fields = ['claim__claim_number', 'vendor_name', 'receipt_number', 'file_name']
    readonly_fields = ['file_name', 'file_size', 'file_type', 'uploaded_by', 'uploaded_at', 'verified_by', 'verified_at']
    date_hierarchy = 'receipt_date'
    
    fieldsets = (
        ('Claim & File', {
            'fields': ('claim', 'file', 'file_name', 'file_size', 'file_type')
        }),
        ('Receipt Details', {
            'fields': ('amount', 'receipt_date', 'vendor_name', 'receipt_number', 'description')
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_by', 'verified_at', 'verification_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReimbursementHistory)
class ReimbursementHistoryAdmin(admin.ModelAdmin):
    list_display = ['claim', 'previous_status', 'new_status', 'action_by', 'action_timestamp']
    list_filter = ['previous_status', 'new_status', 'action_timestamp']
    search_fields = ['claim__claim_number', 'action_by__username', 'notes']
    readonly_fields = ['claim', 'previous_status', 'new_status', 'action_by', 'action_timestamp', 'previous_amount', 'new_amount', 'notes']
    date_hierarchy = 'action_timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
