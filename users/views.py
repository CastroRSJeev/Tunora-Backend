from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.hashers import make_password
from .models import User, OTP, PendingUser
from .serializers import (
    RegisterSerializer,
    VerifyOTPSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    UserSerializer,
    OnboardingSerializer,
)
from .utils import generate_otp, send_otp_email


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
