"""
Notifications App - URL Configuration
Day 7: Task Notifications & Reminders routes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationPreferenceViewSet, TaskEscalationViewSet

# Create router for viewsets
router = DefaultRouter()
# Register escalations and preferences first to avoid conflicts
router.register(r'escalations', TaskEscalationViewSet, basename='task-escalation')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')
# Register notifications last with empty prefix
router.register(r'', NotificationViewSet, basename='notification')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
]
