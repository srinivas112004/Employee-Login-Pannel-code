from django.contrib import admin
from .models import EmployeeProfile, EmployeeDocument, OnboardingChecklist, EmploymentHistory


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'designation', 'department', 'joining_date', 'onboarding_completed']
    list_filter = ['department', 'onboarding_completed', 'gender', 'marital_status']
    search_fields = ['employee_id', 'user__username', 'user__email', 'designation']
    readonly_fields = ['created_at', 'updated_at', 'onboarding_completed_date']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'reporting_manager', 'employee_id')
        }),
        ('Professional Information', {
            'fields': ('designation', 'department', 'joining_date')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'gender', 'marital_status', 'blood_group')
        }),
        ('Contact Information', {
            'fields': ('phone_primary', 'phone_secondary', 'email_personal', 'current_address', 'permanent_address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')
        }),
        ('Bank Details', {
            'fields': ('bank_account_number', 'bank_name', 'bank_ifsc_code', 'pan_number', 'aadhaar_number')
        }),
        ('Profile Picture', {
            'fields': ('profile_picture',)
        }),
        ('Onboarding Status', {
            'fields': ('onboarding_completed', 'onboarding_completed_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'is_verified', 'verified_by', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'uploaded_at']
    search_fields = ['employee__employee_id', 'employee__user__username']
    readonly_fields = ['uploaded_at', 'updated_at', 'verified_at']


@admin.register(OnboardingChecklist)
class OnboardingChecklistAdmin(admin.ModelAdmin):
    list_display = ['employee', 'task_name', 'status', 'due_date', 'completed_at']
    list_filter = ['status', 'due_date', 'created_at']
    search_fields = ['employee__employee_id', 'task_name', 'task_description']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['employee', 'company_name', 'designation', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'start_date']
    search_fields = ['employee__employee_id', 'company_name', 'designation']
    readonly_fields = ['created_at', 'updated_at']
