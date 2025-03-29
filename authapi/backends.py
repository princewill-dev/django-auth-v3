from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import BlacklistedToken

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication that checks if a token has been blacklisted
    before allowing access.
    """
    
    def get_validated_token(self, raw_token):
        """Check if token is blacklisted before validation"""
        # Check if token is in the blacklist
        if BlacklistedToken.objects.filter(token=raw_token.decode()).exists():
            raise InvalidToken(_("Token is blacklisted due to logout"))
        
        # If not blacklisted, proceed with standard validation
        return super().get_validated_token(raw_token)
