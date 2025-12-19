"""
Admin configuration for Compliance app
"""

from django.contrib import admin
from .models import PolicyCategory, Policy, PolicyAcknowledgment, ComplianceReminder


@admin.register(PolicyCategory)
class PolicyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ['title', 'version', 'category', 'status', 'priority', 'is_mandatory', 'effective_date', 'published_at']
    list_filter = ['status', 'priority', 'is_mandatory', 'category']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'published_by', 'published_at', 'created_at', 'updated_at']
    date_hierarchy = 'effective_date'


@admin.register(PolicyAcknowledgment)
class PolicyAcknowledgmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'policy', 'acknowledged', 'acknowledged_at', 'created_at']
    list_filter = ['acknowledged', 'acknowledged_at']
    search_fields = ['user__email', 'policy__title']
    readonly_fields = ['acknowledged_at', 'created_at', 'updated_at']


@admin.register(ComplianceReminder)
class ComplianceReminderAdmin(admin.ModelAdmin):
    list_display = ['user', 'policy', 'reminder_count', 'sent_at']
    list_filter = ['sent_at']
    search_fields = ['user__email', 'policy__title']
