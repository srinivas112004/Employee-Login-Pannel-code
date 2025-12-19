"""
JWT Authentication Middleware for WebSocket Connections
Handles token-based authentication for Django Channels
"""

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from authentication.models import User
from urllib.parse import parse_qs


class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware to authenticate WebSocket connections using JWT tokens
    Supports both query parameter (?token=...) and Authorization header
    """
    
    async def __call__(self, scope, receive, send):
        # Get token from query string or headers
        token = None
        
        # Try to get token from query parameters
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        if 'token' in query_params:
            token = query_params['token'][0]
        
        # If not in query params, try headers
        if not token:
            headers = dict(scope.get('headers', []))
            auth_header = headers.get(b'authorization', b'').decode()
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Authenticate user with token
        if token:
            scope['user'] = await self.get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_token(self, token):
        """
        Validate JWT token and return user
        """
        try:
            # Decode and validate token
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            
            # Get user from database
            user = User.objects.get(id=user_id)
            return user
        
        except (InvalidToken, TokenError, User.DoesNotExist):
            return AnonymousUser()


def JWTAuthMiddlewareStack(inner):
    """
    Wrapper function to apply JWT auth middleware
    Usage: JWTAuthMiddlewareStack(URLRouter(...))
    """
    return JWTAuthMiddleware(inner)
