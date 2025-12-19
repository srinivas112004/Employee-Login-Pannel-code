"""
WebSocket URL routing for chat app
Day 13-14: Real-time Chat with WebSockets and Channels
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket endpoint for chat rooms
    # ws://localhost:8000/ws/chat/<room_id>/
    re_path(r'ws/chat/(?P<room_id>[0-9a-f]{24})/$', consumers.ChatConsumer.as_asgi()),
    
    # WebSocket endpoint for online status
    # ws://localhost:8000/ws/online/
    re_path(r'ws/online/$', consumers.OnlineStatusConsumer.as_asgi()),
    
    # WebSocket endpoint for channel broadcasts (Day 14)
    # ws://localhost:8000/ws/channel/<channel_id>/
    re_path(r'ws/channel/(?P<channel_id>[0-9a-f]{24})/$', consumers.ChannelBroadcastConsumer.as_asgi()),
]
