from django.http import JsonResponse
from django.urls.exceptions import Resolver404

class JSONError404Middleware:
    """Middleware to convert 404 errors to JSON responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Return the response as is if it's not a 404
        if response.status_code != 404:
            return response
            
        # Check if request is an API request (simple check - can be customized)
        if '/api/' in request.path:
            # Convert to JSON response
            return JsonResponse({
                'success': False,
                'message': 'Resource not found',
                'error': {
                    'type': 'NotFound',
                    'details': f'The requested URL {request.path} was not found.'
                }
            }, status=404)
            
        return response
    
    def process_exception(self, request, exception):
        # Handle Resolver404 exceptions specifically
        if isinstance(exception, Resolver404):
            # Check if request is an API request
            if '/api/' in request.path:
                return JsonResponse({
                    'success': False,
                    'message': 'Resource not found',
                    'error': {
                        'type': 'NotFound',
                        'details': f'The requested URL {request.path} was not found.'
                    }
                }, status=404)
        # Let other exceptions pass through to other middleware or exception handlers
        return None
