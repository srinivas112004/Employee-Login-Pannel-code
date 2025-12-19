from django.contrib import admin
from .models import Shift, Attendance, AttendanceRegularization, WorkFromHomeRequest


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time', 'total_hours', 'grace_period_minutes', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'status', 'check_in_time', 'check_out_time', 'work_hours', 'is_late']
    list_filter = ['status', 'is_late', 'date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['work_hours', 'overtime_hours', 'is_late', 'late_by_minutes']
    date_hierarchy = 'date'


@admin.register(AttendanceRegularization)
class AttendanceRegularizationAdmin(admin.ModelAdmin):
    list_display = ['requested_by', 'attendance', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['requested_by__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WorkFromHomeRequest)
class WorkFromHomeRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'status', 'created_at']
    list_filter = ['status', 'date']
    search_fields = ['user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
