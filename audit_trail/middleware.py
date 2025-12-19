"""
Activity Logging Middleware for tracking all API requests
"""

import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from .mongodb_utils import activity_log_manager

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_action_from_method(method):
    """Map HTTP method to action"""
    action_map = {
        'GET': 'READ',
        'POST': 'CREATE',
        'PUT': 'UPDATE',
        'PATCH': 'UPDATE',
        'DELETE': 'DELETE',
    }
    return action_map.get(method, method)


def extract_model_info(path):
    """Extract model name from API path"""
    # Parse path like /api/employees/123/ -> model: Employee, id: 123
    parts = [p for p in path.split('/') if p]
    
    if len(parts) >= 2 and parts[0] == 'api':
        model_name = parts[1].rstrip('s').title()  # employees -> Employee
        object_id = parts[2] if len(parts) > 2 and parts[2].isdigit() else None
        return model_name, object_id
    
    return None, None


class ActivityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API activities to MongoDB
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Skip logging for these paths
        self.skip_paths = [
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Skip logging for these endpoints to reduce noise
        self.skip_endpoints = [
            '/api/logs/activity/',
            '/api/logs/audit/',
            '/api/logs/search/',
        ]
    
    def should_log(self, request):
        """Check if request should be logged"""
        path = request.path
        
        # Skip non-API paths
        for skip_path in self.skip_paths:
            if path.startswith(skip_path):
                return False
        
        # Skip log viewing endpoints to prevent recursion
        for skip_endpoint in self.skip_endpoints:
            if path.startswith(skip_endpoint):
                return False
        
        # Only log API requests
        if not path.startswith('/api/'):
            return False
        
        return True
    
    def process_request(self, request):
        """Store start time for response time calculation"""
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log the request/response to MongoDB"""
        
        # Check if we should log this request
        if not self.should_log(request):
            return response
        
        # Calculate response time
        response_time = None
        if hasattr(request, '_start_time'):
            response_time = int((time.time() - request._start_time) * 1000)  # in milliseconds
        
        # Get user information
        user = getattr(request, 'user', None)
        user_id = None
        user_email = None
        user_name = None
        
        if user and not isinstance(user, AnonymousUser):
            user_id = user.id
            user_email = getattr(user, 'email', None)
            user_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or user_email
        
        # Get request data
        request_data = None
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                if hasattr(request, 'body') and request.body:
                    request_data = json.loads(request.body.decode('utf-8'))
                    # Remove sensitive fields
                    if isinstance(request_data, dict):
                        for sensitive_field in ['password', 'token', 'secret']:
                            if sensitive_field in request_data:
                                request_data[sensitive_field] = '***REDACTED***'
        except:
            pass
        
        # Get response data
        response_data = None
        error_message = None
        try:
            if hasattr(response, 'content') and response.content:
                response_data = json.loads(response.content.decode('utf-8'))
                # Extract error message if present
                if response.status_code >= 400:
                    if isinstance(response_data, dict):
                        error_message = response_data.get('detail') or response_data.get('error') or str(response_data)
                    else:
                        error_message = str(response_data)
        except:
            pass
        
        # Extract model and object info from path
        model_name, object_id = extract_model_info(request.path)
        
        # Create log entry
        try:
            activity_log_manager.create_log(
                user_id=user_id,
                user_email=user_email,
                user_name=user_name,
                action=get_action_from_method(request.method),
                method=request.method,
                endpoint=request.path,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                status_code=response.status_code,
                response_time=response_time,
                request_data=request_data,
                response_data=response_data if response.status_code >= 400 else None,  # Only log errors
                error_message=error_message,
                model_name=model_name,
                object_id=object_id,
                metadata={
                    'query_params': dict(request.GET),
                    'content_type': request.content_type,
                }
            )
        except Exception as e:
            logger.error(f"Failed to log activity: {str(e)}")
        
        return response
