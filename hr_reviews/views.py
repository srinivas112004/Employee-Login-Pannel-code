"""
Views for Performance Reviews & Feedback - Day 19
Role-based permissions:
- Admin/HR: Full access to all review cycles and reviews
- Manager: Can create reviews for their team, provide manager reviews
- Employee: Can view their own reviews, submit self-assessments, provide peer feedback
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from .models import ReviewCycle, Review, SelfAssessment, ManagerReview, PeerFeedback
from .serializers import (
    ReviewCycleSerializer, ReviewCycleListSerializer,
    ReviewSerializer, ReviewListSerializer,
    SelfAssessmentSerializer, ManagerReviewSerializer, PeerFeedbackSerializer
)
from authentication.permissions import IsAdminOrHR, IsManager


class ReviewCycleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Review Cycles
    - Admin/HR: Full CRUD access
    - Manager: Read access to active cycles
    - Employee: Read access to cycles they're part of
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'review_type']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            # Admin/HR can see all cycles
            return ReviewCycle.objects.all()
        elif user.role == 'manager':
            # Managers can see active cycles or cycles they created
            return ReviewCycle.objects.filter(
                Q(status='active') | Q(created_by=user)
            ).distinct()
        else:
            # Employees can see cycles they're part of
            return ReviewCycle.objects.filter(participants=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewCycleListSerializer
        return ReviewCycleSerializer
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Only Admin/HR can create review cycles"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can create review cycles'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only Admin/HR or creator can update review cycles"""
        instance = self.get_object()
        if request.user.role not in ['admin', 'hr'] and instance.created_by != request.user:
            return Response(
                {'error': 'Only Admin/HR or creator can update this review cycle'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR can delete review cycles"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can delete review cycles'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a review cycle (Admin/HR only)"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can activate review cycles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        cycle = self.get_object()
        cycle.status = 'active'
        cycle.save()
        
        return Response({
            'message': f'Review cycle "{cycle.name}" activated successfully',
            'cycle': ReviewCycleSerializer(cycle).data
        })
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a review cycle (Admin/HR only)"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can complete review cycles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        cycle = self.get_object()
        cycle.status = 'completed'
        cycle.save()
        
        return Response({
            'message': f'Review cycle "{cycle.name}" completed successfully',
            'cycle': ReviewCycleSerializer(cycle).data
        })
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a review cycle"""
        cycle = self.get_object()
        
        total_participants = cycle.participants.count()
        total_reviews = cycle.reviews.count()
        
        # Count reviews by status
        reviews_by_status = {}
        for status_choice, _ in Review.STATUS_CHOICES:
            reviews_by_status[status_choice] = cycle.reviews.filter(status=status_choice).count()
        
        # Count completed assessments
        self_assessments_count = SelfAssessment.objects.filter(review__cycle=cycle).count()
        manager_reviews_count = ManagerReview.objects.filter(review__cycle=cycle).count()
        peer_feedbacks_count = PeerFeedback.objects.filter(review__cycle=cycle).count()
        
        return Response({
            'cycle': cycle.name,
            'total_participants': total_participants,
            'total_reviews': total_reviews,
            'reviews_by_status': reviews_by_status,
            'self_assessments_completed': self_assessments_count,
            'manager_reviews_completed': manager_reviews_count,
            'peer_feedbacks_submitted': peer_feedbacks_count,
            'completion_rate': f"{(total_reviews / total_participants * 100) if total_participants > 0 else 0:.1f}%"
        })


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Reviews
    - Admin/HR: Full CRUD access
    - Manager: Can create/view reviews for their team
    - Employee: Can view their own reviews
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cycle', 'status', 'employee']
    search_fields = ['employee__first_name', 'employee__last_name', 'employee__username']
    ordering_fields = ['created_at', 'updated_at', 'overall_rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            # Admin/HR can see all reviews
            queryset = Review.objects.all()
        elif user.role == 'manager':
            # Managers can see reviews for their team or reviews they're assigned as reviewer
            queryset = Review.objects.filter(
                Q(employee__manager=user) | Q(reviewer=user)
            ).distinct()
        else:
            # Employees can see their own reviews
            queryset = Review.objects.filter(employee=user)
        
        # Prefetch related data for performance
        queryset = queryset.select_related(
            'cycle', 'employee', 'reviewer', 
            'self_assessment', 'manager_review'
        ).prefetch_related('peer_feedbacks')
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        return ReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Only Admin/HR or Manager can create reviews"""
        if request.user.role not in ['admin', 'hr', 'manager']:
            return Response(
                {'error': 'Only Admin/HR or Manager can create reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Managers can only create reviews for their team
        if request.user.role == 'manager':
            employee_id = request.data.get('employee')
            from authentication.models import User
            try:
                employee = User.objects.get(id=employee_id)
                if employee.manager != request.user:
                    return Response(
                        {'error': 'You can only create reviews for your team members'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except User.DoesNotExist:
                pass  # Will be caught by serializer validation
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only Admin/HR or reviewer can update review"""
        instance = self.get_object()
        if request.user.role not in ['admin', 'hr'] and instance.reviewer != request.user:
            return Response(
                {'error': 'Only Admin/HR or assigned reviewer can update this review'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR can delete reviews"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can delete reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def calculate_rating(self, request, pk=None):
        """Calculate overall rating from all sub-reviews"""
        review = self.get_object()
        
        # Only Admin/HR or reviewer can calculate rating
        if request.user.role not in ['admin', 'hr'] and review.reviewer != request.user:
            return Response(
                {'error': 'Only Admin/HR or assigned reviewer can calculate rating'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        overall_rating = review.calculate_overall_rating()
        
        if overall_rating is None:
            return Response(
                {'error': 'No sub-reviews available to calculate rating'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Overall rating calculated successfully',
            'overall_rating': float(overall_rating),
            'review': ReviewSerializer(review).data
        })
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's own reviews"""
        reviews = Review.objects.filter(employee=request.user).select_related(
            'cycle', 'reviewer', 'self_assessment', 'manager_review'
        ).prefetch_related('peer_feedbacks')
        
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_reviews(self, request):
        """Get reviews pending action from current user"""
        user = request.user
        pending = []
        
        if user.role == 'manager':
            # Manager reviews pending
            pending = Review.objects.filter(
                reviewer=user,
                status__in=['pending_manager', 'in_progress']
            ).select_related('cycle', 'employee')
        else:
            # Employee's own reviews pending self-assessment
            pending = Review.objects.filter(
                employee=user,
                status='pending_self'
            ).select_related('cycle', 'reviewer')
        
        serializer = ReviewListSerializer(pending, many=True)
        return Response(serializer.data)


class SelfAssessmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Self-Assessments
    - Admin/HR: Full access
    - Employee: Can create/update their own self-assessment
    - Manager: Can view their team's self-assessments
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['review__cycle', 'review__employee']
    ordering_fields = ['submitted_at', 'updated_at']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            return SelfAssessment.objects.all().select_related('review__employee', 'review__cycle')
        elif user.role == 'manager':
            # Managers can see self-assessments of their team
            return SelfAssessment.objects.filter(
                review__employee__manager=user
            ).select_related('review__employee', 'review__cycle')
        else:
            # Employees can see only their own self-assessments
            return SelfAssessment.objects.filter(
                review__employee=user
            ).select_related('review__cycle')
    
    serializer_class = SelfAssessmentSerializer
    
    def create(self, request, *args, **kwargs):
        """Employees can only create self-assessment for their own review"""
        review_id = request.data.get('review')
        
        try:
            review = Review.objects.get(id=review_id)
            
            # Check if employee owns this review
            if review.employee != request.user:
                return Response(
                    {'error': 'You can only create self-assessment for your own review'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if review cycle allows self-assessment
            if not review.cycle.is_self_review_open:
                return Response(
                    {'error': 'Self-assessment deadline has passed for this review cycle'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = super().create(request, *args, **kwargs)
        
        # Update review status
        review.status = 'pending_manager'
        review.save()
        
        return response
    
    def update(self, request, *args, **kwargs):
        """Only employee or Admin/HR can update self-assessment"""
        instance = self.get_object()
        
        if request.user.role not in ['admin', 'hr'] and instance.review.employee != request.user:
            return Response(
                {'error': 'You can only update your own self-assessment'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR can delete self-assessments"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can delete self-assessments'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ManagerReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Manager Reviews
    - Admin/HR: Full access
    - Manager: Can create/update reviews for their team
    - Employee: Can view their own manager review
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['review__cycle', 'review__employee']
    ordering_fields = ['submitted_at', 'updated_at']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            return ManagerReview.objects.all().select_related('review__employee', 'review__reviewer', 'review__cycle')
        elif user.role == 'manager':
            # Managers can see reviews they've given
            return ManagerReview.objects.filter(
                review__reviewer=user
            ).select_related('review__employee', 'review__cycle')
        else:
            # Employees can see their own manager reviews
            return ManagerReview.objects.filter(
                review__employee=user
            ).select_related('review__reviewer', 'review__cycle')
    
    serializer_class = ManagerReviewSerializer
    
    def create(self, request, *args, **kwargs):
        """Only Manager or Admin/HR can create manager review"""
        if request.user.role not in ['admin', 'hr', 'manager']:
            return Response(
                {'error': 'Only Manager or Admin/HR can create manager reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        review_id = request.data.get('review')
        
        try:
            review = Review.objects.get(id=review_id)
            
            # Check if user is the assigned reviewer
            if request.user.role == 'manager' and review.reviewer != request.user:
                return Response(
                    {'error': 'You can only create manager review for reviews assigned to you'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if review cycle allows manager review
            if not review.cycle.is_manager_review_open:
                return Response(
                    {'error': 'Manager review deadline has passed for this review cycle'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        response = super().create(request, *args, **kwargs)
        
        # Update review status
        if review.cycle.peer_review_deadline:
            review.status = 'pending_peer'
        else:
            review.status = 'completed'
            review.completed_at = timezone.now()
        review.save()
        
        return response
    
    def update(self, request, *args, **kwargs):
        """Only reviewer or Admin/HR can update manager review"""
        instance = self.get_object()
        
        if request.user.role not in ['admin', 'hr'] and instance.review.reviewer != request.user:
            return Response(
                {'error': 'You can only update your own manager reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR can delete manager reviews"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin/HR can delete manager reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class PeerFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Peer Feedback
    - Admin/HR: Full access
    - Employee: Can create peer feedback for colleagues, view feedback they've given
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['review__cycle', 'review__employee', 'peer']
    ordering_fields = ['submitted_at', 'updated_at']
    ordering = ['-submitted_at']
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            # Admin/HR can see all feedback
            return PeerFeedback.objects.all().select_related('review__employee', 'review__cycle', 'peer')
        elif user.role == 'manager':
            # Managers can see feedback for their team (non-anonymous) or feedback they've given
            return PeerFeedback.objects.filter(
                Q(review__employee__manager=user, is_anonymous=False) | Q(peer=user)
            ).select_related('review__employee', 'review__cycle', 'peer')
        else:
            # Employees can see feedback they've given
            return PeerFeedback.objects.filter(peer=user).select_related('review__employee', 'review__cycle')
    
    serializer_class = PeerFeedbackSerializer
    
    def create(self, request, *args, **kwargs):
        """Employees can create peer feedback for colleagues"""
        review_id = request.data.get('review')
        
        try:
            review = Review.objects.get(id=review_id)
            
            # Can't provide feedback for own review
            if review.employee == request.user:
                return Response(
                    {'error': 'You cannot provide peer feedback for your own review'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if review cycle allows peer feedback
            if not review.cycle.is_peer_review_open:
                return Response(
                    {'error': 'Peer review deadline has passed for this review cycle'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Set peer to current user
        request.data['peer'] = request.user.id
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only feedback giver or Admin/HR can update peer feedback"""
        instance = self.get_object()
        
        if request.user.role not in ['admin', 'hr'] and instance.peer != request.user:
            return Response(
                {'error': 'You can only update your own peer feedback'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR or feedback giver can delete peer feedback"""
        instance = self.get_object()
        
        if request.user.role not in ['admin', 'hr'] and instance.peer != request.user:
            return Response(
                {'error': 'You can only delete your own peer feedback'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_feedback(self, request):
        """Get all feedback current user has given"""
        feedback = PeerFeedback.objects.filter(peer=request.user).select_related('review__employee', 'review__cycle')
        serializer = self.get_serializer(feedback, many=True)
        return Response(serializer.data)
