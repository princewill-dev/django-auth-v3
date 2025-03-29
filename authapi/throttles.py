from rest_framework.throttling import SimpleRateThrottle

class SignupRateThrottle(SimpleRateThrottle):
    scope = 'signup'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }

class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        email = request.data.get('email')
        if email:
            ident = email
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

# Keep the OTPVerificationRateThrottle if you still need it
class OTPVerificationRateThrottle(SimpleRateThrottle):
    scope = 'otp_verification'

    def get_cache_key(self, request, view):
        email = request.data.get('email')
        if email:
            ident = email
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
