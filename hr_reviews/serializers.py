"""
Serializers for Performance Reviews & Feedback - Day 19
"""

from rest_framework import serializers
from django.utils import timezone
from .models import ReviewCycle, Review, SelfAssessment, ManagerReview, PeerFeedback
from authentication.models import User


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for nested representations"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'role']


class ReviewCycleSerializer(serializers.ModelSerializer):
    """Serializer for ReviewCycle"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_self_review_open = serializers.ReadOnlyField()
    is_manager_review_open = serializers.ReadOnlyField()
    is_peer_review_open = serializers.ReadOnlyField()
    
    class Meta:
        model = ReviewCycle
        fields = [
            'id', 'name', 'review_type', 'description',
            'start_date', 'end_date', 
            'self_review_deadline', 'manager_review_deadline', 'peer_review_deadline',
            'status', 'participants', 'participant_count', 'review_count',
            'is_self_review_open', 'is_manager_review_open', 'is_peer_review_open',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_review_count(self, obj):
        return obj.reviews.count()
    
    def validate(self, data):
        """Validate review cycle dates"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        self_deadline = data.get('self_review_deadline')
        manager_deadline = data.get('manager_review_deadline')
        peer_deadline = data.get('peer_review_deadline')
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date")
        
        if end_date and self_deadline and self_deadline < end_date:
            raise serializers.ValidationError("Self-review deadline should be after review period ends")
        
        if self_deadline and manager_deadline and manager_deadline < self_deadline:
            raise serializers.ValidationError("Manager review deadline should be after self-review deadline")
        
        if manager_deadline and peer_deadline and peer_deadline < manager_deadline:
            raise serializers.ValidationError("Peer review deadline should be after manager review deadline")
        
        return data


class ReviewCycleListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing review cycles"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    participant_count = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ReviewCycle
        fields = [
            'id', 'name', 'review_type', 'start_date', 'end_date',
            'self_review_deadline', 'manager_review_deadline', 'status',
            'participant_count', 'review_count', 'created_by_name', 'created_at'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_review_count(self, obj):
        return obj.reviews.count()


class SelfAssessmentSerializer(serializers.ModelSerializer):
    """Serializer for SelfAssessment"""
    employee_name = serializers.CharField(source='review.employee.get_full_name', read_only=True)
    cycle_name = serializers.CharField(source='review.cycle.name', read_only=True)
    
    class Meta:
        model = SelfAssessment
        fields = [
            'id', 'review', 'employee_name', 'cycle_name',
            'accomplishments', 'challenges_faced', 'skills_developed',
            'quality_of_work', 'productivity', 'communication', 'teamwork', 'initiative',
            'goals_achieved', 'goals_for_next_period',
            'overall_rating', 'additional_comments',
            'submitted_at', 'updated_at'
        ]
        read_only_fields = ['submitted_at', 'updated_at']
    
    def validate_review(self, value):
        """Ensure self-assessment doesn't already exist for this review"""
        if self.instance is None:  # Only check on creation
            if hasattr(value, 'self_assessment'):
                raise serializers.ValidationError("Self-assessment already exists for this review")
        return value
    
    def validate(self, data):
        """Validate ratings are consistent with overall rating"""
        if all(k in data for k in ['quality_of_work', 'productivity', 'communication', 'teamwork', 'initiative']):
            avg_rating = (
                data['quality_of_work'] + data['productivity'] + 
                data['communication'] + data['teamwork'] + data['initiative']
            ) / 5
            
            if 'overall_rating' in data:
                if abs(float(data['overall_rating']) - avg_rating) > 1.5:
                    raise serializers.ValidationError(
                        f"Overall rating ({data['overall_rating']}) is too different from average rating ({avg_rating:.2f})"
                    )
        
        return data


class ManagerReviewSerializer(serializers.ModelSerializer):
    """Serializer for ManagerReview"""
    employee_name = serializers.CharField(source='review.employee.get_full_name', read_only=True)
    manager_name = serializers.CharField(source='review.reviewer.get_full_name', read_only=True)
    cycle_name = serializers.CharField(source='review.cycle.name', read_only=True)
    
    class Meta:
        model = ManagerReview
        fields = [
            'id', 'review', 'employee_name', 'manager_name', 'cycle_name',
            'performance_summary', 'strengths', 'areas_for_improvement',
            'quality_of_work', 'productivity', 'communication', 'teamwork', 
            'initiative', 'leadership', 'problem_solving',
            'goals_achievement_comment', 'goals_for_next_period',
            'promotion_recommendation', 'salary_increase_recommendation', 'training_recommendations',
            'overall_rating', 'manager_comments',
            'submitted_at', 'updated_at'
        ]
        read_only_fields = ['submitted_at', 'updated_at']
    
    def validate_review(self, value):
        """Ensure manager review doesn't already exist for this review"""
        if self.instance is None:  # Only check on creation
            if hasattr(value, 'manager_review'):
                raise serializers.ValidationError("Manager review already exists for this review")
        return value
    
    def validate(self, data):
        """Validate ratings are consistent with overall rating"""
        rating_fields = ['quality_of_work', 'productivity', 'communication', 'teamwork', 
                        'initiative', 'leadership', 'problem_solving']
        
        if all(k in data for k in rating_fields):
            avg_rating = sum(data[field] for field in rating_fields) / len(rating_fields)
            
            if 'overall_rating' in data:
                if abs(float(data['overall_rating']) - avg_rating) > 1.5:
                    raise serializers.ValidationError(
                        f"Overall rating ({data['overall_rating']}) is too different from average rating ({avg_rating:.2f})"
                    )
        
        return data


class PeerFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for PeerFeedback"""
    employee_name = serializers.CharField(source='review.employee.get_full_name', read_only=True)
    peer_name = serializers.SerializerMethodField()
    cycle_name = serializers.CharField(source='review.cycle.name', read_only=True)
    
    class Meta:
        model = PeerFeedback
        fields = [
            'id', 'review', 'peer', 'employee_name', 'peer_name', 'cycle_name',
            'collaboration_feedback', 'strengths', 'areas_for_improvement',
            'teamwork', 'communication', 'reliability', 'helpfulness',
            'overall_rating', 'additional_comments', 'is_anonymous',
            'submitted_at', 'updated_at'
        ]
        read_only_fields = ['submitted_at', 'updated_at']
    
    def get_peer_name(self, obj):
        """Return peer name or 'Anonymous' based on is_anonymous flag"""
        if obj.is_anonymous:
            return "Anonymous"
        return obj.peer.get_full_name()
    
    def validate(self, data):
        """Validate peer feedback constraints"""
        # Check for duplicate peer feedback
        if self.instance is None:  # Only check on creation
            review = data.get('review')
            peer = data.get('peer')
            if review and peer and PeerFeedback.objects.filter(review=review, peer=peer).exists():
                raise serializers.ValidationError("You have already provided feedback for this review")
        
        # Validate ratings consistency
        if all(k in data for k in ['teamwork', 'communication', 'reliability', 'helpfulness']):
            avg_rating = (
                data['teamwork'] + data['communication'] + 
                data['reliability'] + data['helpfulness']
            ) / 4
            
            if 'overall_rating' in data:
                if abs(float(data['overall_rating']) - avg_rating) > 1.5:
                    raise serializers.ValidationError(
                        f"Overall rating ({data['overall_rating']}) is too different from average rating ({avg_rating:.2f})"
                    )
        
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for Review with nested assessments"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)
    
    # Nested assessments (read-only for display)
    self_assessment = SelfAssessmentSerializer(read_only=True)
    manager_review = ManagerReviewSerializer(read_only=True)
    peer_feedbacks = PeerFeedbackSerializer(many=True, read_only=True)
    peer_feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'cycle', 'cycle_name', 'employee', 'employee_name', 
            'reviewer', 'reviewer_name', 'overall_rating', 'status',
            'promotion_recommended', 'salary_increase_recommended', 'improvement_plan_required',
            'self_assessment', 'manager_review', 'peer_feedbacks', 'peer_feedback_count',
            'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['overall_rating', 'completed_at', 'created_at', 'updated_at']
    
    def get_peer_feedback_count(self, obj):
        return obj.peer_feedbacks.count()
    
    def validate(self, data):
        """Validate review constraints"""
        # Check for duplicate review in same cycle
        if self.instance is None:  # Only check on creation
            cycle = data.get('cycle')
            employee = data.get('employee')
            if cycle and employee and Review.objects.filter(cycle=cycle, employee=employee).exists():
                raise serializers.ValidationError("Review already exists for this employee in this cycle")
        
        return data


class ReviewListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reviews"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    cycle_name = serializers.CharField(source='cycle.name', read_only=True)
    has_self_assessment = serializers.SerializerMethodField()
    has_manager_review = serializers.SerializerMethodField()
    peer_feedback_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'cycle', 'cycle_name', 'employee', 'employee_name',
            'reviewer', 'reviewer_name', 'overall_rating', 'status',
            'has_self_assessment', 'has_manager_review', 'peer_feedback_count',
            'created_at', 'updated_at'
        ]
    
    def get_has_self_assessment(self, obj):
        return hasattr(obj, 'self_assessment')
    
    def get_has_manager_review(self, obj):
        return hasattr(obj, 'manager_review')
    
    def get_peer_feedback_count(self, obj):
        return obj.peer_feedbacks.count()
