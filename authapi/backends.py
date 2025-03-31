from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import BlacklistedToken
from rest_framework.authentication import BaseAuthentication

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that checks if a token has been blacklisted
    before allowing access.
    """
    
    def authenticate(self, request):
        header = self.get_header(request)
        
        # If no Auth header exists, return None (unauthenticated) without raising an exception
        # This allows public endpoints to work without authentication
        if header is None:
            return None
            
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
            
        try:
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            # For endpoints with AllowAny permission, we don't want to raise an exception
            # This allows the request to proceed to permission checking
            return None
    
    def get_validated_token(self, raw_token):
        """Check if token is blacklisted before validation"""
        # Check if token is in the blacklist
        if BlacklistedToken.objects.filter(token=raw_token.decode()).exists():
            raise InvalidToken(_("Token is blacklisted due to logout"))
        
        # If not blacklisted, proceed with standard validation
        return super().get_validated_token(raw_token)
