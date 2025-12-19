"""
Authentication App - Admin Configuration
Registers models with Django admin interface.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Device, UserSession, EmailOTP, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for User model.
    """
    list_display = ['email', 'employee_id', 'get_full_name', 'role', 'department', 'is_active', 'date_joined']
    list_filter = ['role', 'department', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-date_joined']
    
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'alternate_phone', 'date_of_birth', 'profile_picture', 'bio')
        }),
        ('Employment Details', {
            'fields': ('employee_id', 'role', 'department', 'designation', 'manager', 'date_of_joining')
        }),
        ('Security & Verification (Day 2)', {
            'fields': ('is_email_verified', 'two_factor_enabled')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'role', 'employee_id'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login']


# ==============================================================================
# DAY 3 ADMIN - Device and Session Management
# ==============================================================================

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """
    Admin interface for Device model.
    """
    list_display = ['user', 'device_name', 'device_type', 'browser', 'os', 'is_trusted', 'last_used_at', 'registered_at']
    list_filter = ['device_type', 'is_trusted', 'registered_at']
    search_fields = ['user__email', 'device_name', 'device_fingerprint', 'last_ip']
    ordering = ['-last_used_at']
    readonly_fields = ['registered_at', 'last_used_at', 'device_fingerprint']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = ['user', 'device', 'ip_address', 'location', 'login_at', 'is_active', 'is_suspicious']
    list_filter = ['is_active', 'is_suspicious', 'login_at']
    search_fields = ['user__email', 'ip_address', 'session_token']
    ordering = ['-login_at']
    readonly_fields = ['login_at', 'last_activity', 'logout_at', 'session_token']


# ==============================================================================
# DAY 2 ADMIN - OTP and Password Reset
# ==============================================================================

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    """
    Admin interface for EmailOTP model.
    """
    list_display = ['user', 'otp_code', 'purpose', 'is_used', 'created_at', 'expires_at', 'is_valid_display']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__email', 'otp_code']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'expires_at', 'otp_code']
    
    def is_valid_display(self, obj):
        """Display if OTP is valid."""
        return obj.is_valid()
    is_valid_display.short_description = 'Is Valid'
    is_valid_display.boolean = True


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for PasswordResetToken model.
    """
    list_display = ['user', 'token_preview', 'is_used', 'created_at', 'expires_at', 'is_valid_display']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'expires_at', 'token']
    
    def token_preview(self, obj):
        """Display first 20 characters of token."""
        return f"{obj.token[:20]}..."
    token_preview.short_description = 'Token'
    
    def is_valid_display(self, obj):
        """Display if token is valid."""
        return obj.is_valid()
    is_valid_display.short_description = 'Is Valid'
    is_valid_display.boolean = True
