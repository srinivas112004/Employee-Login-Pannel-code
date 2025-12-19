"""
Authentication App - URL Configuration
Maps URLs to views.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    # Day 1 views
    # UserRegistrationView,  # REMOVED: Only superusers create users
    UserLoginView,
    UserProfileView,
    ChangePasswordView,
    UserListView,
    LogoutView,
    # Day 2 views
    SendOTPView,
    VerifyOTPView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    Enable2FAView,
    ResendVerificationEmailView,
    # Day 3 views
    UserDevicesView,
    RemoveDeviceView,
    TrustDeviceView,
    ActiveSessionsView,
    LogoutSessionView,
    LogoutAllSessionsView,
)

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints (Day 1)
    # path('register/', UserRegistrationView.as_view(), name='register'),  # REMOVED: Only superusers can create users via Django admin
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Profile endpoints (Day 1)
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # User management (Day 1)
    path('users/', UserListView.as_view(), name='user_list'),
    
    # Day 2: OTP & Email Verification
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Day 2: Password Reset
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Day 2: Two-Factor Authentication
    path('2fa/toggle/', Enable2FAView.as_view(), name='enable_2fa'),
    
    # Day 3: Device Management
    path('devices/', UserDevicesView.as_view(), name='user_devices'),
    path('devices/<int:device_id>/', RemoveDeviceView.as_view(), name='remove_device'),
    path('devices/trust/', TrustDeviceView.as_view(), name='trust_device'),
    
    # Day 3: Session Management
    path('sessions/', ActiveSessionsView.as_view(), name='active_sessions'),
    path('sessions/<int:session_id>/logout/', LogoutSessionView.as_view(), name='logout_session'),
    path('sessions/logout-all/', LogoutAllSessionsView.as_view(), name='logout_all_sessions'),
]
