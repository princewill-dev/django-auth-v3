from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
import random
import traceback
import jwt
from datetime import datetime, timedelta
from hashlib import sha256

from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache

from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import SimpleRateThrottle, AnonRateThrottle, UserRateThrottle

from rest_framework_simplejwt.tokens import RefreshToken, TokenError, AccessToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken

from .models import User, BlacklistedToken
from .throttles import SignupRateThrottle, LoginRateThrottle, OTPVerificationRateThrottle
from .token_utils import get_tokens_for_user
from .backends import CustomJWTAuthentication
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer, 
    UserProfileUpdateSerializer,
    OTPVerificationSerializer,
    PasswordResetSerializer,
)

User = get_user_model()

class CustomTokenRefreshView(TokenRefreshView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        try:
            token = RefreshToken(refresh_token)
            user = token.user
            if user.last_activity and timezone.now() - user.last_activity > timedelta(hours=1):
                return Response({"detail": "Token has expired due to inactivity."}, status=status.HTTP_401_UNAUTHORIZED)
            return Response(get_tokens_for_user(user))
        except InvalidToken:
            return Response({"detail": "Invalid token."}, status=status.HTTP_401_UNAUTHORIZED)

class UserRegistrationView(APIView):
    throttle_classes = [AnonRateThrottle, SignupRateThrottle]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Create user with is_active=False (default in our model)
            user = serializer.save()
            
            # Generate and save 6-digit OTP
            otp = str(random.randint(100000, 999999))
            user.set_email_verification_code(otp)
            
            # Send OTP via email
            send_mail(
                'Account Verification',
                f'Thank you for registering! Your verification code is: {otp}\n\nThis code will expire in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            response_data = {
                'success': True,
                'message': 'Registration successful. Please verify your email with the OTP sent to your inbox.',
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response({
            'success': False,
            'message': 'Registration failed',
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class OTPVerificationView(APIView):
    throttle_classes = [AnonRateThrottle, OTPVerificationRateThrottle]
    
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            try:
                user = User.objects.get(email=email)
                
                # Check if user is already verified
                if user.is_active:
                    return Response({
                        'success': False,
                        'message': 'Account is already verified'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Verify OTP
                if user.email_verification_code == otp and user.is_email_verification_code_valid():
                    # Activate user account
                    user.is_active = True
                    user.email_verification_code = None
                    user.email_verification_code_created_at = None
                    user.save()
                    
                    # Generate tokens for auto-login after verification
                    tokens = get_tokens_for_user(user)
                    
                    return Response({
                        'success': True,
                        'message': 'Account verified successfully',
                        'tokens': tokens,
                        'user': UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Invalid or expired verification code'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'User not found with this email'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': False,
            'message': 'Validation failed',
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class ResendOTPView(APIView):
    throttle_classes = [AnonRateThrottle, OTPVerificationRateThrottle]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'success': False,
                'message': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already verified
            if user.is_active:
                return Response({
                    'success': False,
                    'message': 'Account is already verified'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate and save new OTP
            otp = str(random.randint(100000, 999999))
            user.set_email_verification_code(otp)
            
            # Send OTP via email
            send_mail(
                'Account Verification',
                f'Your new verification code is: {otp}\n\nThis code will expire in 10 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return Response({
                'success': True,
                'message': 'Verification code has been resent to your email'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found with this email'
            }, status=status.HTTP_404_NOT_FOUND)

class UserLoginView(APIView):
    throttle_classes = [AnonRateThrottle, LoginRateThrottle]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if user.is_active:
                    # Update last activity
                    user.last_activity = timezone.now()
                    user.save(update_fields=['last_activity'])
                    
                    # Generate tokens
                    tokens = get_tokens_for_user(user)
                    
                    return Response({
                        'success': True,
                        'message': 'Login successful',
                        'tokens': tokens,
                        'user': UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'message': 'Account not verified',
                        'error': 'Please verify your email before logging in',
                        'user_exists': True,
                        'email': email
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
class UserProfileView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request):
        """Get user profile details"""
        user = request.user
        serializer = UserSerializer(user)
        return Response({
            'success': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user profile details"""
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'message': 'Profile update failed',
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request):
        """Partially update user profile details"""
        return self.put(request)

class UserLogoutView(APIView):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def post(self, request):
        try:
            # Get the auth header and extract the token
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                
                # Decode token to get expiry time
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                    options={"verify_signature": True}
                )
                
                # Calculate token expiry datetime with timezone awareness
                expiry_timestamp = decoded_token['exp']
                expiry = timezone.make_aware(
                    datetime.fromtimestamp(expiry_timestamp),
                    timezone=timezone.get_current_timezone()
                )
                
                # Add token to blacklist
                BlacklistedToken.objects.create(
                    token=token,
                    user=request.user,
                    expires_at=expiry
                )
                
                # Update user's last activity time
                user = request.user
                user.last_activity = timezone.now()
                user.save(update_fields=['last_activity'])
                
                return Response({
                    'success': True,
                    'message': 'Logged out successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Invalid authorization header format'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except (jwt.PyJWTError, Exception) as e:
            return Response({
                'success': False,
                'message': f'Error processing logout: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(APIView):
    throttle_classes = [OTPVerificationRateThrottle]
    permission_classes = [AllowAny]
    authentication_classes = []  # Empty list means no authentication is attempted

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'success': False,
                'message': 'Validation failed',
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            # Generate OTP for password reset
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            user.set_email_verification_code(otp)

            # Send email with OTP for password reset
            subject = 'Password Reset OTP'
            message = f'Your OTP for password reset is: {otp}. It will expire in 10 minutes.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                'success': True,
                'message': 'Password reset OTP sent successfully'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found',
                'error': 'No account exists with this email address'
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Validation failed',
                'error': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']
        confirm_password = serializer.validated_data['confirm_password']

        if new_password != confirm_password:
            return Response({
                'success': False,
                'message': 'Passwords do not match',
                'error': 'New password and confirm password must be the same'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            
            if user.email_verification_code == otp and user.is_email_verification_code_valid():
                user.set_password(new_password)
                user.email_verification_code = None
                user.email_verification_code_created_at = None
                user.save()
                return Response({
                    'success': True,
                    'message': 'Password reset successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'OTP validation failed',
                    'error': 'Invalid or expired OTP'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found',
                'error': 'No account exists with this email address'
            }, status=status.HTTP_404_NOT_FOUND)
