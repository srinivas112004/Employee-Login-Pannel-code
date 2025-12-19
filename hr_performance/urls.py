"""
URL Configuration for Performance Management - Day 18
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GoalCategoryViewSet, GoalViewSet, KPIViewSet,
    ProgressUpdateViewSet, MilestoneViewSet
)

router = DefaultRouter()
router.register(r'categories', GoalCategoryViewSet, basename='goal-category')
router.register(r'goals', GoalViewSet, basename='goal')
router.register(r'kpis', KPIViewSet, basename='kpi')
router.register(r'progress-updates', ProgressUpdateViewSet, basename='progress-update')
router.register(r'milestones', MilestoneViewSet, basename='milestone')

urlpatterns = [
    path('', include(router.urls)),
]
