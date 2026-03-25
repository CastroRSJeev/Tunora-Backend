import random
import string
from django.core.mail import send_mail
from django.conf import settings


def generate_otp():
    """Generate a random 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email, otp_code):
    """Send OTP verification email to the user."""
    subject = 'Tunora — Verify Your Email'
    message = (
        f'Welcome to Tunora! 🎵\n\n'
        f'Your verification code is: {otp_code}\n\n'
        f'This code expires in {getattr(settings, "OTP_EXPIRY_MINUTES", 5)} minutes.\n\n'
        f'If you did not create an account, please ignore this email.'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )


def send_password_reset_email(email, otp_code):
    """Send password reset OTP email to the user."""
    subject = 'Tunora — Reset Your Password'
    message = (
        f'Hello! 🎵\n\n'
        f'You requested to reset your password.\n\n'
        f'Your reset code is: {otp_code}\n\n'
        f'This code expires in {getattr(settings, "OTP_EXPIRY_MINUTES", 5)} minutes.\n\n'
        f'If you did not request this, please ignore this email.'
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
