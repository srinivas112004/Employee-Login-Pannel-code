"""
Authentication App - User Model
This file defines the custom User model with roles and additional fields.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
import string
from datetime import timedelta


class UserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    instead of username.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model for Employee Management System
    Uses email instead of username for authentication.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('hr', 'HR'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
        ('intern', 'Intern'),
    ]
    
    # Basic Information
    email = models.EmailField(unique=True, db_index=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    # Role and Department
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Contact Information
    phone = models.CharField(max_length=15, blank=True, null=True)
    alternate_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Profile
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Employment Details
    date_of_joining = models.DateField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)  # Day 2: Email verification
    two_factor_enabled = models.BooleanField(default=False)  # Day 2: 2FA toggle
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Device Management (for Day 3)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    last_login_device = models.CharField(max_length=255, blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == 'admin'
    
    @property
    def is_hr(self):
        """Check if user is HR."""
        return self.role == 'hr'
    
    @property
    def is_manager(self):
        """Check if user is a manager."""
        return self.role == 'manager'


class Device(models.Model):
    """
    Day 3: Model to track user devices for security purposes.
    Uses device fingerprinting (SHA256 hash of User-Agent + IP).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_devices')
    device_fingerprint = models.CharField(max_length=64)  # SHA256 hash (unique per user via unique_together)
    device_name = models.CharField(max_length=255)  # e.g., "Chrome on Windows"
    device_type = models.CharField(max_length=50)  # mobile, desktop, tablet
    browser = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    last_used_at = models.DateTimeField(auto_now=True)
    last_ip = models.GenericIPAddressField()
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_devices'
        verbose_name = 'User Device'
        verbose_name_plural = 'User Devices'
        ordering = ['-last_used_at']
        unique_together = [['user', 'device_fingerprint']]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_name}"


class EmailOTP(models.Model):
    """
    Model to store OTP for email verification and 2FA.
    OTPs expire after 10 minutes.
    """
    OTP_PURPOSE_CHOICES = [
        ('email_verification', 'Email Verification'),
        ('login_2fa', 'Login 2FA'),
        ('password_reset', 'Password Reset'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=OTP_PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'email_otps'
        verbose_name = 'Email OTP'
        verbose_name_plural = 'Email OTPs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.purpose} - {self.otp_code}"
    
    def save(self, *args, **kwargs):
        """Auto-generate OTP code and expiry time on creation."""
        if not self.pk:  # Only on creation
            # Generate 6-digit OTP
            self.otp_code = ''.join(random.choices(string.digits, k=6))
            # Set expiry to 10 minutes from now
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def generate_otp(cls, user, purpose):
        """Generate a new OTP for the user."""
        # Invalidate all previous OTPs for same purpose
        cls.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)
        # Create new OTP
        return cls.objects.create(user=user, purpose=purpose)


class PasswordResetToken(models.Model):
    """
    Model to store password reset tokens.
    Tokens expire after 1 hour.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=100, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'password_reset_tokens'
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.token[:20]}..."
    
    def save(self, *args, **kwargs):
        """Auto-generate token and expiry time on creation."""
        if not self.pk:  # Only on creation
            # Generate random token
            self.token = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
            # Set expiry to 1 hour from now
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if token is still valid (not used and not expired)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    @classmethod
    def generate_token(cls, user):
        """Generate a new reset token for the user."""
        # Invalidate all previous tokens
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        # Create new token
        return cls.objects.create(user=user)


class UserSession(models.Model):
    """
    Model to track active user sessions for security.
    Tracks login/logout times, IP address, location, device used.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, 
                               related_name='sessions')
    
    session_token = models.CharField(max_length=255, unique=True, 
                                     help_text="JWT refresh token or session ID")
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=200, blank=True, 
                               help_text="City, Country from IP geolocation")
    user_agent = models.TextField(blank=True)
    
    login_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    logout_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Security flags
    is_suspicious = models.BooleanField(default=False, 
                                       help_text="Flagged for unusual activity")
    flagged_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-login_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address} - {self.login_at}"
    
    def logout(self):
        """Mark session as logged out."""
        self.is_active = False
        self.logout_at = timezone.now()
        self.save()
    
    @property
    def duration(self):
        """Calculate session duration."""
        if self.logout_at:
            return self.logout_at - self.login_at
        return timezone.now() - self.login_at
