"""
Authentication Middleware
Validates active sessions on each authenticated request.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.deprecation import MiddlewareMixin
from .models import UserSession


class ActiveSessionMiddleware(MiddlewareMixin):
    """
    Middleware to check if the user's session is still active.
    If a session has been logged out (is_active=False), reject the request.
    """
    
    def process_request(self, request):
        """
        Check if the request has a valid active session.
        This runs before the view is called.
        """
        # Skip for unauthenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            # Try to authenticate using JWT
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '').strip()
                
                try:
                    # Authenticate the token
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(token)
                    user = jwt_auth.get_user(validated_token)
                    
                    # Check if this session is still active
                    session = UserSession.objects.filter(
                        user=user,
                        session_token=token,
                        is_active=True
                    ).first()
                    
                    if not session:
                        # Session has been logged out
                        from django.http import JsonResponse
                        return JsonResponse(
                            {
                                'error': 'Session has been terminated',
                                'code': 'SESSION_LOGGED_OUT',
                                'detail': 'This session has been logged out from another device.'
                            },
                            status=401
                        )
                    
                    # Set the user on the request
                    request.user = user
                    
                except Exception:
                    # Token validation failed, let the normal auth handle it
                    pass
        
        return None  # Continue processing
