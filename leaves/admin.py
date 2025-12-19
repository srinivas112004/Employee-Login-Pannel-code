from django.contrib import admin
from .models import Leave, LeaveType, LeaveBalance


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'default_days', 'requires_document', 'is_active']
    list_filter = ['is_active', 'requires_document']
    search_fields = ['name', 'code']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'year', 'total_days', 'used_days', 'available_days']
    list_filter = ['year', 'leave_type']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['available_days']


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'created_at']
    list_filter = ['status', 'leave_type', 'start_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'reason']
    readonly_fields = ['total_days', 'created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        ('Leave Information', {
            'fields': ('user', 'leave_type', 'start_date', 'end_date', 'total_days', 'reason', 'document')
        }),
        ('Status', {
            'fields': ('status', 'applied_to', 'approved_by', 'approved_at', 'rejection_reason')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
