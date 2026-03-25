from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from .models import User, OTP, PendingUser, PasswordResetOTP
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    UserSerializer,
    OnboardingSerializer,
    ForgotPasswordSerializer,
    VerifyResetOTPSerializer,
    ResetPasswordSerializer,
)
from .utils import generate_otp, send_otp_email, send_password_reset_email


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Save registration data to PendingUser and send OTP.
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    email = serializer.validated_data['email']
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    role = serializer.validated_data.get('role', 'listener')

    # Hash password now
    hashed_pw = make_password(password)
    otp_code = generate_otp()

    # Create or update pending user
    PendingUser.objects.filter(email=email).delete()
    PendingUser.objects.create(
        email=email,
        username=username,
        password=hashed_pw,
        role=role,
        otp_code=otp_code
    )

    try:
        send_otp_email(email, otp_code)
    except Exception:
        pass

    return Response(
        {
            'message': 'Registration initiated. Please verify your email with the OTP sent.',
            'email': email,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """
    Verify OTP from PendingUser and create the actual User.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp']

    try:
        pending = PendingUser.objects.get(email=email)
    except PendingUser.DoesNotExist:
        # Check if already verified
        if User.objects.filter(email=email, is_verified=True).exists():
            return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)
        return Response({'error': 'No pending registration found for this email.'}, status=status.HTTP_404_NOT_FOUND)

    if pending.otp_code != otp_code:
        return Response({'error': 'Invalid OTP code.'}, status=status.HTTP_400_BAD_REQUEST)

    if pending.is_expired():
        return Response({'error': 'OTP has expired. Please register again.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the actual User
    user = User.objects.create(
        email=pending.email,
        username=pending.username,
        password=pending.password, # Already hashed
        role=pending.role,
        is_verified=True
    )
    
    # Delete pending data
    pending.delete()

    return Response(
        {'message': 'Email verified successfully. You can now log in.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    """
    Resend OTP to PendingUser.
    """
    serializer = ResendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    if User.objects.filter(email=email, is_verified=True).exists():
        return Response({'message': 'Email is already verified.'}, status=status.HTTP_200_OK)

    try:
        pending = PendingUser.objects.get(email=email)
    except PendingUser.DoesNotExist:
        return Response({'error': 'No pending registration found.'}, status=status.HTTP_404_NOT_FOUND)

    # Generate new OTP
    otp_code = generate_otp()
    pending.otp_code = otp_code
    pending.created_at = timezone.now() # Reset expiry
    pending.save()

    try:
        send_otp_email(email, otp_code)
    except Exception:
        pass

    return Response(
        {'message': 'A new OTP has been sent to your email.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate user and return JWT tokens + user data.

    POST /api/auth/login/
    Body: { email, password }
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response(
        {
            'message': 'Login successful.',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'user': UserSerializer(user).data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Blacklist refresh token to log user out.

    POST /api/auth/logout/
    Body: { refresh }
    Headers: Authorization: Bearer <access_token>
    """
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response(
            {'error': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        return Response(
            {'error': 'Invalid or expired refresh token.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {'message': 'Logged out successfully.'},
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Return the currently authenticated user's data."""
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def onboarding_view(request):
    """
    Update the user's interests during onboarding.
    Requires at least 3 genres and 3 artists.
    """
    serializer = OnboardingSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        # Return full user profile after update
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    """
    Send a password-reset OTP to the user's email.

    POST /api/auth/forgot-password/
    Body: { email }
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']

    # Check if user exists and is verified
    try:
        user = User.objects.get(email=email, is_verified=True)
    except User.DoesNotExist:
        # Don't reveal whether the email exists — always return success
        return Response(
            {'message': 'If an account with that email exists, a reset code has been sent.'},
            status=status.HTTP_200_OK,
        )

    # Delete any previous reset OTPs for this email
    PasswordResetOTP.objects.filter(email=email).delete()

    otp_code = generate_otp()
    PasswordResetOTP.objects.create(email=email, otp_code=otp_code)

    try:
        send_password_reset_email(email, otp_code)
    except Exception:
        pass

    return Response(
        {'message': 'If an account with that email exists, a reset code has been sent.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_otp_view(request):
    """
    Verify the password-reset OTP.

    POST /api/auth/verify-reset-otp/
    Body: { email, otp }
    """
    serializer = VerifyResetOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp']

    try:
        reset_otp = PasswordResetOTP.objects.get(email=email, otp_code=otp_code, is_verified=False)
    except PasswordResetOTP.DoesNotExist:
        return Response({'error': 'Invalid OTP code.'}, status=status.HTTP_400_BAD_REQUEST)

    if reset_otp.is_expired():
        reset_otp.delete()
        return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

    # Mark as verified so it can be used in reset-password step
    reset_otp.is_verified = True
    reset_otp.save()

    return Response(
        {'message': 'OTP verified. You can now reset your password.'},
        status=status.HTTP_200_OK,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    """
    Reset the user's password after OTP verification.

    POST /api/auth/reset-password/
    Body: { email, otp, new_password, confirm_password }
    """
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    otp_code = serializer.validated_data['otp']
    new_password = serializer.validated_data['new_password']

    # Verify the OTP was previously verified
    try:
        reset_otp = PasswordResetOTP.objects.get(email=email, otp_code=otp_code, is_verified=True)
    except PasswordResetOTP.DoesNotExist:
        return Response({'error': 'Invalid or unverified OTP.'}, status=status.HTTP_400_BAD_REQUEST)

    if reset_otp.is_expired():
        reset_otp.delete()
        return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

    # Update user password
    try:
        user = User.objects.get(email=email, is_verified=True)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    user.password = make_password(new_password)
    user.save()

    # Clean up
    PasswordResetOTP.objects.filter(email=email).delete()

    return Response(
        {'message': 'Password reset successfully. You can now log in.'},
        status=status.HTTP_200_OK,
    )
