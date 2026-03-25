from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for user profile data (returned in login response)."""
    id = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'bio', 'avatar',
                  'favourite_genres', 'favourite_moods', 'favourite_artists',
                  'is_verified', 'is_banned', 'onboarding_completed', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined', 'is_verified']


class OnboardingSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user interests during onboarding.
    Enforces minimum selections in the view.
    """
    class Meta:
        model = User
        fields = ['favourite_genres', 'favourite_moods', 'favourite_artists', 'onboarding_completed']

    def validate_favourite_genres(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Please select at least 3 genres.")
        return value

    def validate_favourite_artists(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Please select at least 3 artists.")
        return value


from .models import User, PendingUser


class RegisterSerializer(serializers.Serializer):
    """
    Validates registration data for PendingUser creation.
    """
    email = serializers.EmailField()
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    role = serializers.CharField(required=False, default='listener')

    def validate_role(self, value):
        if value not in ['listener', 'artist']:
            raise serializers.ValidationError('Role must be either "listener" or "artist".')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Validates email + OTP code for email verification."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class ResendOTPSerializer(serializers.Serializer):
    """Validates email for resending OTP."""
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    """Validates login credentials and checks email verification status."""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No account found with this email.'})

        # Check if email is verified
        if not user.is_verified:
            raise serializers.ValidationError(
                {'email': 'Email not verified. Please verify your email first.'}
            )

        # Authenticate
        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError({'password': 'Invalid password.'})

        if not user.is_active:
            raise serializers.ValidationError({'email': 'This account has been deactivated.'})

        attrs['user'] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Validates email for forgot password request."""
    email = serializers.EmailField()


class VerifyResetOTPSerializer(serializers.Serializer):
    """Validates email + OTP for password reset verification."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    """Validates new password for password reset."""
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs
