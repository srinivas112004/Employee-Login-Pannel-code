"""
URL configuration for Audit Trail app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityLogViewSet, AuditLogViewSet

router = DefaultRouter()
router.register(r'activity', ActivityLogViewSet, basename='activity-log')
router.register(r'audit', AuditLogViewSet, basename='audit-log')

urlpatterns = [
    path('', include(router.urls)),
]
