"""
Authentication App - Views
Handles API requests and responses for authentication.
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserListSerializer,
    # Day 2 serializers
    SendOTPSerializer,
    VerifyOTPSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    Enable2FASerializer,
)
from .models import EmailOTP, PasswordResetToken
from .email_utils import send_otp_email, send_password_reset_email, send_welcome_email

User = get_user_model()


class UserRegistrationView(APIView):
    """
    API endpoint for user registration.
    Allows anyone to create a new user account.
    
    POST /api/auth/register/
    """
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    
    def post(self, request):
        """
        Register a new user.
        
        Request Body:
        {
            "email": "user@company.com",
            "password": "SecurePass123!",
            "password2": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "role": "employee",
            "employee_id": "EMP001",
            "department": "Engineering",
            "designation": "Developer"
        }
        """
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'employee_id': user.employee_id,
                    'is_email_verified': user.is_email_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    API endpoint for user login.
    Returns JWT tokens on successful authentication.
    
    POST /api/auth/login/
    """
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    
    def post(self, request):
        """
        Login user and return JWT tokens.
        
        Request Body:
        {
            "email": "user@company.com",
            "password": "SecurePass123!"
        }
        """
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Check if 2FA is enabled for this user
            if user.two_factor_enabled:
                # Send OTP for 2FA verification instead of logging in
                otp = EmailOTP.generate_otp(user=user, purpose='login_2fa')
                
                # Send OTP email
                from .email_utils import send_otp_email
                email_sent = send_otp_email(user.email, otp.otp_code, 'login_2fa')
                
                if not email_sent:
                    return Response(
                        {"error": "Failed to send 2FA code. Please try again."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Return response indicating 2FA is required
                return Response({
                    'requires_2fa': True,
                    'message': 'Two-factor authentication required. OTP sent to your email.',
                    'email': user.email,
                    'user_id': user.id,
                }, status=status.HTTP_200_OK)
            
            # If 2FA is not enabled, proceed with normal login
            # Update last login info
            from django.utils import timezone
            from authentication.device_utils import (
                get_device_info_from_request,
                generate_device_fingerprint,
                is_new_device,
                get_client_ip
            )
            from authentication.models import Device, UserSession
            
            user.last_login = timezone.now()
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login', 'last_login_ip'])
            
            # Get device information
            device_info = get_device_info_from_request(request)
            device_fingerprint = device_info['device_fingerprint']
            
            # Check if device exists or create new
            device, created = Device.objects.get_or_create(
                user=user,
                device_fingerprint=device_fingerprint,
                defaults={
                    'device_name': device_info['device_name'],
                    'device_type': device_info['device_type'],
                    'browser': device_info['browser'],
                    'browser_version': device_info['browser_version'],
                    'os': device_info['os'],
                    'os_version': device_info['os_version'],
                    'last_ip': device_info['ip_address'],
                }
            )
            
            # Update device last used if not newly created
            if not created:
                device.last_used_at = timezone.now()
                device.last_ip = device_info['ip_address']
                device.save(update_fields=['last_used_at', 'last_ip'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Create session record
            UserSession.objects.create(
                user=user,
                device=device,
                session_token=access_token,
                ip_address=device_info['ip_address'],
                location='',  # Can integrate with IP geolocation service later
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_active=True
            )
            
            # Send notification if new device
            notification_message = ""
            if created:
                notification_message = " Login from a new device detected."
            
            return Response({
                'message': f'Login successful{notification_message}',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.get_full_name(),
                    'role': user.role,
                    'employee_id': user.employee_id,
                    'department': user.department,
                    'designation': user.designation,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None,
                    'is_email_verified': user.is_email_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': access_token,
                },
                'device': {
                    'device_id': device.id,
                    'device_name': device.device_name,
                    'is_new': created,
                    'is_trusted': device.is_trusted
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserProfileView(APIView):
    """
    API endpoint for user profile.
    GET: Retrieve current user's profile
    PUT: Update current user's profile
    
    GET/PUT /api/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer
    
    def get(self, request):
        """
        Get current user's profile.
        
        Headers:
        Authorization: Bearer <access_token>
        """
        serializer = self.serializer_class(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """
        Update current user's profile.
        
        Request Body: Any fields from UserProfileSerializer
        (except read-only fields like email, role, employee_id)
        """
        serializer = self.serializer_class(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    """
    API endpoint for changing password.
    
    POST /api/auth/change-password/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        """
        Change user password.
        
        Request Body:
        {
            "old_password": "OldPass123!",
            "new_password": "NewPass123!",
            "new_password2": "NewPass123!"
        }
        """
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    """
    API endpoint to list all users.
    Used for dropdowns, assignments, etc.
    
    GET /api/auth/users/
    Query params: ?role=manager&department=Engineering
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserListSerializer
    queryset = User.objects.filter(is_active=True)
    
    def get_queryset(self):
        """
        Filter users based on query parameters.
        """
        queryset = super().get_queryset()
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department=department)
        
        # Search by name or email
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(employee_id__icontains=search)
            )
        
        return queryset


class LogoutView(APIView):
    """
    API endpoint for user logout.
    Blacklists the refresh token.
    
    POST /api/auth/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Logout user by blacklisting refresh token.
        
        Request Body:
        {
            "refresh": "<refresh_token>"
        }
        """
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "message": "Logout successful"
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
# DAY 2 VIEWS - Email OTP, 2FA, Password Reset
# ==============================================================================

class SendOTPView(APIView):
    """
    API endpoint to send OTP to user's email.
    Used for email verification, 2FA, and password reset.
    
    POST /api/auth/send-otp/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Send OTP to user's email.
        
        Request Body:
        {
            "email": "user@company.com",
            "purpose": "email_verification" | "login_2fa" | "password_reset"
        }
        """
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(email=email)
            
            # Generate OTP
            otp = EmailOTP.generate_otp(user=user, purpose=purpose)
            
            # Send OTP email
            email_sent = send_otp_email(user.email, otp.otp_code, purpose)
            
            if not email_sent:
                return Response(
                    {"error": "Failed to send email. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                "message": f"OTP sent successfully to {email}",
                "otp_expires_in": "10 minutes",
                "purpose": purpose
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyOTPView(APIView):
    """
    API endpoint to verify OTP.
    
    POST /api/auth/verify-otp/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Verify OTP code.
        
        Request Body:
        {
            "email": "user@company.com",
            "otp_code": "123456",
            "purpose": "email_verification" | "login_2fa" | "password_reset"
        }
        """
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        purpose = serializer.validated_data['purpose']
        
        try:
            user = User.objects.get(email=email)
            
            # Get the latest unused OTP for this purpose
            otp = EmailOTP.objects.filter(
                user=user,
                purpose=purpose,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp:
                return Response(
                    {"error": "No valid OTP found. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OTP matches and is valid
            if otp.otp_code != otp_code:
                return Response(
                    {"error": "Invalid OTP code"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not otp.is_valid():
                return Response(
                    {"error": "OTP has expired. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # Perform purpose-specific actions
            response_data = {"message": "OTP verified successfully"}
            
            if purpose == 'email_verification':
                user.is_email_verified = True
                user.save()
                # Send welcome email
                send_welcome_email(user.email, user.get_full_name())
                response_data['email_verified'] = True
            
            elif purpose == 'login_2fa':
                # Complete 2FA login - generate tokens and create session
                from authentication.device_utils import (
                    get_device_info_from_request,
                    get_client_ip
                )
                from authentication.models import Device, UserSession
                
                # Update last login
                user.last_login = timezone.now()
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_login', 'last_login_ip'])
                
                # Get device information
                device_info = get_device_info_from_request(request)
                device_fingerprint = device_info['device_fingerprint']
                
                # Get or create device
                device, created = Device.objects.get_or_create(
                    user=user,
                    device_fingerprint=device_fingerprint,
                    defaults={
                        'device_name': device_info['device_name'],
                        'device_type': device_info['device_type'],
                        'browser': device_info['browser'],
                        'browser_version': device_info['browser_version'],
                        'os': device_info['os'],
                        'os_version': device_info['os_version'],
                        'last_ip': device_info['ip_address'],
                    }
                )
                
                if not created:
                    device.last_used_at = timezone.now()
                    device.last_ip = device_info['ip_address']
                    device.save(update_fields=['last_used_at', 'last_ip'])
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                # Create session
                UserSession.objects.create(
                    user=user,
                    device=device,
                    session_token=access_token,
                    ip_address=device_info['ip_address'],
                    location='',
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    is_active=True
                )
                
                # Return login response with tokens
                response_data = {
                    'message': '2FA verification successful. Login complete.',
                    '2fa_verified': True,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': user.get_full_name(),
                        'role': user.role,
                        'employee_id': user.employee_id,
                        'department': user.department,
                        'designation': user.designation,
                        'profile_picture': user.profile_picture.url if user.profile_picture else None,
                        'is_email_verified': user.is_email_verified,
                        'two_factor_enabled': user.two_factor_enabled,
                    },
                    'tokens': {
                        'refresh': str(refresh),
                        'access': access_token,
                    },
                    'device': {
                        'device_id': device.id,
                        'device_name': device.device_name,
                        'is_new': created,
                        'is_trusted': device.is_trusted
                    }
                }
            
            elif purpose == 'password_reset':
                # Generate password reset token
                reset_token = PasswordResetToken.generate_token(user)
                response_data['reset_token'] = reset_token.token
                response_data['message'] = "OTP verified. Use the token to reset your password."
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetRequestView(APIView):
    """
    API endpoint to request password reset.
    Sends OTP to user's email.
    
    POST /api/auth/password-reset/request/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Request password reset.
        
        Request Body:
        {
            "email": "user@company.com"
        }
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate OTP for password reset
            otp = EmailOTP.generate_otp(user=user, purpose='password_reset')
            
            # Send OTP email
            email_sent = send_otp_email(user.email, otp.otp_code, 'password_reset')
            
            if not email_sent:
                return Response(
                    {"error": "Failed to send email. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                "message": f"Password reset OTP sent to {email}",
                "next_step": "Verify OTP to get reset token"
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security)
            return Response({
                "message": "If an account exists with this email, a reset OTP has been sent."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PasswordResetConfirmView(APIView):
    """
    API endpoint to reset password using token.
    
    POST /api/auth/password-reset/confirm/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Reset password with token.
        
        Request Body:
        {
            "token": "<reset_token>",
            "new_password": "NewSecurePass123!",
            "new_password2": "NewSecurePass123!"
        }
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token_value = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Get reset token
            reset_token = PasswordResetToken.objects.get(token=token_value)
            
            if not reset_token.is_valid():
                return Response(
                    {"error": "Token is invalid or expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            return Response({
                "message": "Password reset successful. You can now login with your new password."
            }, status=status.HTTP_200_OK)
        
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class Enable2FAView(APIView):
    """
    API endpoint to enable/disable 2FA on user account.
    
    POST /api/auth/2fa/toggle/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Enable or disable 2FA.
        
        Request Body:
        {
            "enable": true | false
        }
        """
        serializer = Enable2FASerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        enable = serializer.validated_data['enable']
        
        user.two_factor_enabled = enable
        user.save()
        
        return Response({
            "message": f"2FA {'enabled' if enable else 'disabled'} successfully",
            "two_factor_enabled": user.two_factor_enabled
        }, status=status.HTTP_200_OK)


class ResendVerificationEmailView(APIView):
    """
    API endpoint to resend email verification OTP.
    
    POST /api/auth/resend-verification/
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Resend verification email.
        
        Request Body:
        {
            "email": "user@example.com"
        }
        """
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal if user exists or not (security)
            return Response(
                {"message": "If an account exists with this email and is not verified, a verification email has been sent."},
                status=status.HTTP_200_OK
            )
        
        if user.is_email_verified:
            # Don't reveal that user is already verified (security)
            return Response(
                {"message": "If an account exists with this email and is not verified, a verification email has been sent."},
                status=status.HTTP_200_OK
            )
        
        try:
            # Generate new OTP
            otp = EmailOTP.generate_otp(user=user, purpose='email_verification')
            
            # Send OTP email
            email_sent = send_otp_email(user.email, otp.otp_code, 'email_verification')
            
            if not email_sent:
                return Response(
                    {"error": "Failed to send email. Please try again."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                "message": f"Verification OTP sent to {email}",
                "otp_expires_in": "10 minutes"
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ==============================================================================
# DAY 3: Device & Session Management Views
# ==============================================================================

class UserDevicesView(APIView):
    """
    API endpoint to list all devices registered to the current user.
    
    GET /api/auth/devices/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all devices for current user."""
        from authentication.models import Device
        from authentication.serializers import DeviceSerializer
        
        devices = Device.objects.filter(user=request.user)
        serializer = DeviceSerializer(devices, many=True)
        
        return Response({
            "devices": serializer.data,
            "total_devices": devices.count()
        }, status=status.HTTP_200_OK)


class RemoveDeviceView(APIView):
    """
    API endpoint to remove a device from user's registered devices.
    
    DELETE /api/auth/devices/{device_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, device_id):
        """Remove a device."""
        from authentication.models import Device, UserSession
        
        try:
            device = Device.objects.get(id=device_id, user=request.user)
            
            # Also logout all sessions from this device
            UserSession.objects.filter(device=device, is_active=True).update(
                is_active=False,
                logout_at=timezone.now()
            )
            
            device.delete()
            
            return Response({
                "message": "Device removed successfully"
            }, status=status.HTTP_200_OK)
        
        except Device.DoesNotExist:
            return Response(
                {"error": "Device not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class TrustDeviceView(APIView):
    """
    API endpoint to mark a device as trusted or untrusted.
    
    POST /api/auth/devices/trust/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark device as trusted/untrusted."""
        from authentication.models import Device
        from authentication.serializers import TrustDeviceSerializer
        
        serializer = TrustDeviceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        device_id = serializer.validated_data['device_id']
        trust = serializer.validated_data['trust']
        
        try:
            device = Device.objects.get(id=device_id, user=request.user)
            device.is_trusted = trust
            device.save()
            
            return Response({
                "message": f"Device {'trusted' if trust else 'untrusted'} successfully",
                "device_id": device_id,
                "is_trusted": device.is_trusted
            }, status=status.HTTP_200_OK)
        
        except Device.DoesNotExist:
            return Response(
                {"error": "Device not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class ActiveSessionsView(APIView):
    """
    API endpoint to list all active sessions for current user.
    
    GET /api/auth/sessions/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all active sessions."""
        from authentication.models import UserSession
        from authentication.serializers import UserSessionSerializer
        
        sessions = UserSession.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('device')
        
        serializer = UserSessionSerializer(
            sessions, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            "sessions": serializer.data,
            "total_sessions": sessions.count()
        }, status=status.HTTP_200_OK)


class LogoutSessionView(APIView):
    """
    API endpoint to logout from a specific session.
    
    POST /api/auth/sessions/{session_id}/logout/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """Logout from specific session."""
        from authentication.models import UserSession
        
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            
            session.logout()
            
            return Response({
                "message": "Session logged out successfully"
            }, status=status.HTTP_200_OK)
        
        except UserSession.DoesNotExist:
            return Response(
                {"error": "Session not found or already logged out"},
                status=status.HTTP_404_NOT_FOUND
            )


class LogoutAllSessionsView(APIView):
    """
    API endpoint to logout from all sessions except current.
    
    POST /api/auth/sessions/logout-all/
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Logout from all sessions except current."""
        from authentication.models import UserSession
        
        # Get the current session token from the request
        auth_header = request.headers.get('Authorization', '')
        current_token = auth_header.replace('Bearer ', '').strip() if auth_header.startswith('Bearer ') else None
        
        if not current_token:
            return Response(
                {"error": "No authorization token found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find current session by matching the session_token
        current_session = UserSession.objects.filter(
            user=request.user,
            session_token=current_token,
            is_active=True
        ).first()
        
        # Get all active sessions except current
        if current_session:
            other_sessions = UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).exclude(id=current_session.id)
        else:
            # If no current session found, logout all sessions
            other_sessions = UserSession.objects.filter(
                user=request.user,
                is_active=True
            )
        
        count = other_sessions.count()
        
        # Logout all other sessions
        other_sessions.update(
            is_active=False,
            logout_at=timezone.now()
        )
        
        return Response({
            "message": f"Logged out from {count} other sessions",
            "sessions_logged_out": count
        }, status=status.HTTP_200_OK)
