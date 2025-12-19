from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShiftViewSet, AttendanceViewSet, AttendanceRegularizationViewSet,
    WorkFromHomeRequestViewSet
)

router = DefaultRouter()
router.register(r'shifts', ShiftViewSet, basename='shift')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'regularizations', AttendanceRegularizationViewSet, basename='regularization')
router.register(r'wfh-requests', WorkFromHomeRequestViewSet, basename='wfh-request')

urlpatterns = [
    path('', include(router.urls)),
]
