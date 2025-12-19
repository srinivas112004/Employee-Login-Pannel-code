"""
URL configuration for documents app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentCategoryViewSet, DocumentViewSet, DocumentShareViewSet

router = DefaultRouter()
router.register(r'categories', DocumentCategoryViewSet, basename='document-category')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'shares', DocumentShareViewSet, basename='document-share')

urlpatterns = [
    path('', include(router.urls)),
]
