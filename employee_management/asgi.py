"""
ASGI config for employee_management project.
Day 13: Updated to support WebSockets with Django Channels + JWT Authentication
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_management.settings')

# Initialize Django ASGI application early to populate apps
django_asgi_app = get_asgi_application()

# Import routing and JWT middleware after Django is initialized
from chat import routing as chat_routing
from chat.middleware import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(
            chat_routing.websocket_urlpatterns
        )
    ),
})
