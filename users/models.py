from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    """Custom manager for User model with email-based authentication."""

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with role-based access control.
    Roles: listener, artist, admin
    """
    ROLE_CHOICES = (
        ('listener', 'Listener'),
        ('artist', 'Artist'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='listener')

    # Profile fields
    bio = models.TextField(blank=True, default='')
    avatar = models.URLField(blank=True, default='')  # Cloudinary URL

    # Onboarding preferences (stored as JSON for flexibility)
    favourite_genres = models.JSONField(default=list, blank=True)
    favourite_moods = models.JSONField(default=list, blank=True)
    favourite_artists = models.JSONField(default=list, blank=True)
    onboarding_completed = models.BooleanField(default=False)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.username} ({self.role})'


class OTP(models.Model):
    """
    Stores email OTP codes for user verification.
    Codes expire after OTP_EXPIRY_MINUTES (default: 5 min).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']

    def is_expired(self):
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        return timezone.now() > self.created_at + timezone.timedelta(minutes=expiry_minutes)

    def __str__(self):
        return f'OTP {self.code} for {self.user.email}'


class PendingUser(models.Model):
    """
    Temporary storage for registration data before OTP verification.
    """
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # Hashed password
    role = models.CharField(max_length=10)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pending_users'

    def is_expired(self):
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        return timezone.now() > self.created_at + timezone.timedelta(minutes=expiry_minutes)

    def __str__(self):
        return f'Pending {self.email} ({self.otp_code})'


class PasswordResetOTP(models.Model):
    """
    Stores OTP codes for password reset requests.
    """
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'password_reset_otps'
        ordering = ['-created_at']

    def is_expired(self):
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 5)
        return timezone.now() > self.created_at + timezone.timedelta(minutes=expiry_minutes)

    def __str__(self):
        return f'PasswordReset OTP {self.otp_code} for {self.email}'
