from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveViewSet, LeaveTypeViewSet, LeaveBalanceView

router = DefaultRouter()
router.register(r'leaves', LeaveViewSet, basename='leave')
router.register(r'types', LeaveTypeViewSet, basename='leave-type')

urlpatterns = [
    path('balance/', LeaveBalanceView.as_view(), name='leave-balance'),
    path('', include(router.urls)),
]
