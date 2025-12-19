from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeProfileViewSet,
    EmployeeDocumentViewSet,
    OnboardingChecklistViewSet,
    EmploymentHistoryViewSet
)

router = DefaultRouter()
router.register(r'employees', EmployeeProfileViewSet, basename='employee-profile')
router.register(r'documents', EmployeeDocumentViewSet, basename='employee-document')
router.register(r'onboarding', OnboardingChecklistViewSet, basename='onboarding-checklist')
router.register(r'employment-history', EmploymentHistoryViewSet, basename='employment-history')

urlpatterns = [
    path('', include(router.urls)),
]
