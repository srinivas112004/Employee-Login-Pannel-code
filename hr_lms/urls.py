"""
URL Configuration for Learning Management System (LMS)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet, EnrollmentViewSet, ModuleProgressViewSet,
    # Day 21 ViewSets
    QuizViewSet, QuizQuestionViewSet, CertificateViewSet, SkillViewSet, UserSkillViewSet
)

router = DefaultRouter()
# Day 20 - Core LMS
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'modules', ModuleViewSet, basename='module')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'progress', ModuleProgressViewSet, basename='progress')

# Day 21 - Quiz, Certificates, Skills
router.register(r'quizzes', QuizViewSet, basename='quiz')
router.register(r'quiz-questions', QuizQuestionViewSet, basename='quiz-question')
router.register(r'certificates', CertificateViewSet, basename='certificate')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'user-skills', UserSkillViewSet, basename='user-skill')

urlpatterns = [
    path('', include(router.urls)),
]
