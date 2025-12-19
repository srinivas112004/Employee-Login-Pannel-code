"""
Email Utility Functions
Handles sending emails for OTP, verification, and password reset.
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_otp_email(user_email, otp_code, purpose):
    """
    Send OTP email to user.
    
    Args:
        user_email (str): Recipient email address
        otp_code (str): 6-digit OTP code
        purpose (str): Purpose of OTP (email_verification, login_2fa, password_reset)
    """
    purpose_titles = {
        'email_verification': 'Email Verification',
        'login_2fa': 'Two-Factor Authentication',
        'password_reset': 'Password Reset',
    }
    
    subject = f'{purpose_titles.get(purpose, "Verification")} - Employee Management System'
    
    message = f"""
Hello,

Your OTP code is: {otp_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Regards,
Employee Management System Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_password_reset_email(user_email, reset_token, user_name):
    """
    Send password reset email with token link.
    
    Args:
        user_email (str): Recipient email address
        reset_token (str): Password reset token
        user_name (str): User's full name
    """
    subject = 'Password Reset Request - Employee Management System'
    
    # In production, this would be your actual domain
    reset_link = f"http://localhost:3000/reset-password/{reset_token}"
    
    message = f"""
Hello {user_name},

We received a request to reset your password.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request a password reset, please ignore this email.

Regards,
Employee Management System Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_welcome_email(user_email, user_name):
    """
    Send welcome email after email verification.
    
    Args:
        user_email (str): Recipient email address
        user_name (str): User's full name
    """
    subject = 'Welcome to Employee Management System'
    
    message = f"""
Hello {user_name},

Welcome to Employee Management System!

Your email has been successfully verified. You can now access all features of the system.

If you have any questions, please contact your HR department.

Regards,
Employee Management System Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
