"""
URL patterns for Performance Reviews & Feedback - Day 19
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReviewCycleViewSet, ReviewViewSet, 
    SelfAssessmentViewSet, ManagerReviewViewSet, PeerFeedbackViewSet
)

router = DefaultRouter()
router.register(r'review-cycles', ReviewCycleViewSet, basename='reviewcycle')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'self-assessments', SelfAssessmentViewSet, basename='selfassessment')
router.register(r'manager-reviews', ManagerReviewViewSet, basename='managerreview')
router.register(r'peer-feedback', PeerFeedbackViewSet, basename='peerfeedback')

urlpatterns = [
    path('', include(router.urls)),
]
