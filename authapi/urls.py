from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    PasswordResetView,
    OTPVerificationView,
    ResendOTPView,
    CustomTokenRefreshView,
    UserLogoutView,
)

app_name = 'authapi'

urlpatterns = [
    # Authentication endpoints
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # OTP verification endpoints
    path('verify-otp/', OTPVerificationView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    
    # User profile endpoint
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Password reset endpoint
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    # Alternative URL for password reset (for better UX)
    path('reset-password/', PasswordResetView.as_view(), name='reset-password'),
]