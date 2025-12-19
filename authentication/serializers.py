"""
Authentication App - Serializers
Converts complex data types (like User objects) to Python datatypes
that can be easily rendered into JSON.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, EmailOTP, PasswordResetToken, Device, UserSession


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Handles password validation and user creation.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'role', 'employee_id', 'department', 'designation', 'phone',
            'date_of_joining', 'manager'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def validate_email(self, value):
        """Validate email is unique and from company domain (optional)."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        
        # Optional: Enforce company email domain
        # if not value.endswith('@company.com'):
        #     raise serializers.ValidationError("Please use your company email.")
        
        return value.lower()
    
    def create(self, validated_data):
        """Create and return a new user."""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Authenticates user credentials.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate user credentials."""
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled."
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                "Must include 'email' and 'password'."
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    Used for retrieving and updating user information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'employee_id', 'first_name', 'last_name', 'full_name',
            'role', 'department', 'designation', 'phone', 'alternate_phone',
            'profile_picture', 'bio', 'date_of_joining', 'date_of_birth',
            'manager', 'manager_name', 'is_active', 'is_email_verified', 
            'two_factor_enabled', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'employee_id', 'role', 'is_email_verified', 
                           'two_factor_enabled', 'date_joined']
    
    def update(self, instance, validated_data):
        """Update user profile."""
        # Don't allow updating sensitive fields through this endpoint
        validated_data.pop('email', None)
        validated_data.pop('role', None)
        validated_data.pop('employee_id', None)
        
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Validate old password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """Validate that new passwords match."""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "New password fields didn't match."
            })
        return attrs
    
    def save(self):
        """Save the new password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (minimal info).
    Used for dropdowns, assignments, etc.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'employee_id', 'full_name', 
            'role', 'department', 'designation', 'profile_picture'
        ]


# ==============================================================================
# DAY 2 SERIALIZERS - OTP, Email Verification, Password Reset
# ==============================================================================

class SendOTPSerializer(serializers.Serializer):
    """
    Serializer for sending OTP to email.
    Used for 2FA and email verification.
    """
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=['email_verification', 'login_2fa', 'password_reset'],
        required=True
    )
    
    def validate_email(self, value):
        """Validate that user exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """
    Serializer for verifying OTP.
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(max_length=6, min_length=6, required=True)
    purpose = serializers.ChoiceField(
        choices=['email_verification', 'login_2fa', 'password_reset'],
        required=True
    )
    
    def validate_email(self, value):
        """Validate that user exists."""
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value
    
    def validate_otp_code(self, value):
        """Validate OTP code format."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    Sends reset link to email.
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate that user exists and is active."""
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("This account is inactive.")
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security)
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset with token.
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs
    
    def validate_token(self, value):
        """Validate that token exists and is valid."""
        try:
            reset_token = PasswordResetToken.objects.get(token=value)
            if not reset_token.is_valid():
                raise serializers.ValidationError("Token is invalid or expired.")
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        return value


class Enable2FASerializer(serializers.Serializer):
    """
    Serializer for enabling 2FA on user account.
    """
    enable = serializers.BooleanField(required=True)
    
    def validate(self, attrs):
        """Add user to context."""
        user = self.context['request'].user
        
        if attrs['enable'] and not user.is_email_verified:
            raise serializers.ValidationError({
                "enable": "Please verify your email before enabling 2FA."
            })
        
        return attrs


# ============================================================================
# DAY 3: Device & Session Management Serializers
# ============================================================================

class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for Device model.
    Shows device information for user's registered devices.
    """
    last_used = serializers.DateTimeField(source='last_used_at', read_only=True)
    registered = serializers.DateTimeField(source='registered_at', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'device_name', 'device_type', 'browser', 'browser_version',
            'os', 'os_version', 'is_trusted', 'last_used', 'registered', 'last_ip'
        ]
        read_only_fields = ['id', 'last_used', 'registered', 'last_ip']


class TrustDeviceSerializer(serializers.Serializer):
    """
    Serializer for marking a device as trusted.
    """
    device_id = serializers.IntegerField(required=True)
    trust = serializers.BooleanField(required=True)


class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for UserSession model.
    Shows active session information.
    """
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    device_type = serializers.CharField(source='device.device_type', read_only=True)
    duration = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSession
        fields = [
            'id', 'device_name', 'device_type', 'ip_address', 'location',
            'login_at', 'last_activity', 'is_active', 'duration', 'is_current'
        ]
        read_only_fields = ['id', 'login_at', 'last_activity', 'is_active']
    
    def get_duration(self, obj):
        """Calculate session duration in human-readable format."""
        duration = obj.duration
        hours = duration.seconds // 3600
        minutes = (duration.seconds % 3600) // 60
        
        if duration.days > 0:
            return f"{duration.days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def get_is_current(self, obj):
        """Check if this is the current session."""
        request = self.context.get('request')
        if not request:
            return False
        
        # Compare IP addresses to identify current session
        from authentication.device_utils import get_client_ip
        current_ip = get_client_ip(request)
        return obj.ip_address == current_ip and obj.is_active
