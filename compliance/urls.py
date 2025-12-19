"""
URL configuration for Compliance app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PolicyCategoryViewSet, PolicyViewSet, PolicyAcknowledgmentViewSet

router = DefaultRouter()
router.register(r'categories', PolicyCategoryViewSet, basename='policy-category')
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'acknowledgments', PolicyAcknowledgmentViewSet, basename='policy-acknowledgment')

urlpatterns = [
    path('', include(router.urls)),
]
