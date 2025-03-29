from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError


def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework that returns consistent JSON responses
    for all exceptions throughout the application.
    """
    # First, get the standard error response from DRF
    response = exception_handler(exc, context)
    
    # If this is a standard REST framework exception, the response will be set and we'll enhance it
    if response is not None:
        error_data = {
            'success': False,
            'message': 'Error occurred',
            'error': {
                'type': exc.__class__.__name__,
                'details': response.data
            }
        }
        
        response.data = error_data
        return response
    
    # Handle Django's built-in exceptions
    if isinstance(exc, Http404):
        error_data = {
            'success': False,
            'message': 'Resource not found',
            'error': {
                'type': 'NotFound',
                'details': str(exc) if str(exc) else 'The requested resource was not found.'
            }
        }
        return Response(error_data, status=status.HTTP_404_NOT_FOUND)
    
    elif isinstance(exc, PermissionDenied):
        error_data = {
            'success': False,
            'message': 'Permission denied',
            'error': {
                'type': 'PermissionDenied',
                'details': str(exc) if str(exc) else 'You do not have permission to perform this action.'
            }
        }
        return Response(error_data, status=status.HTTP_403_FORBIDDEN)
    
    elif isinstance(exc, ValidationError):
        error_data = {
            'success': False,
            'message': 'Validation error',
            'error': {
                'type': 'ValidationError',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
            }
        }
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, IntegrityError):
        error_data = {
            'success': False,
            'message': 'Database integrity error',
            'error': {
                'type': 'IntegrityError',
                'details': str(exc)
            }
        }
        return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
        
    # Handle 500 errors explicitly
    elif isinstance(exc, Exception):
        error_data = {
            'success': False,
            'message': 'Server error',
            'error': {
                'type': 'ServerError',
                'details': str(exc) if str(exc) else 'An unexpected server error occurred.'
            }
        }
        return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Catch-all for any other exceptions that weren't handled above
    error_data = {
        'success': False,
        'message': 'Server error',
        'error': {
            'type': exc.__class__.__name__,
            'details': str(exc) if str(exc) else 'An unexpected error occurred.'
        }
    }
    return Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
