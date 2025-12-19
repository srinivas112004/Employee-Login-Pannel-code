from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChatRoomViewSet, MessageViewSet, UserOnlineStatusViewSet,
    ChatNotificationViewSet, FileUploadViewSet, ChannelViewSet
)

router = DefaultRouter()
router.register(r'rooms', ChatRoomViewSet, basename='chatroom')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'online-status', UserOnlineStatusViewSet, basename='online-status')
router.register(r'notifications', ChatNotificationViewSet, basename='chat-notification')
router.register(r'files', FileUploadViewSet, basename='file-upload')
router.register(r'channels', ChannelViewSet, basename='channel')

urlpatterns = [
    path('', include(router.urls)),
]
