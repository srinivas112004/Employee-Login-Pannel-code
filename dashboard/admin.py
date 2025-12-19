"""
Dashboard App - Admin Configuration
Registers dashboard models with Django admin interface.
"""

from django.contrib import admin
from .models import Announcement, Task, LeaveBalance


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for Announcement model."""
    list_display = ['title', 'priority', 'created_by', 'created_at', 'is_active', 'is_expired']
    list_filter = ['priority', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""
    list_display = ['title', 'assigned_to', 'assigned_by', 'status', 'priority', 'due_date', 'is_overdue']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'assigned_to__email']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    """Admin interface for LeaveBalance model."""
    list_display = ['user', 'leave_type', 'total_days', 'used_days', 'remaining_days', 'year']
    list_filter = ['leave_type', 'year']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['user', 'leave_type']
