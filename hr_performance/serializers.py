"""
Serializers for Performance Management - Day 18
"""

from rest_framework import serializers
from django.utils import timezone
from .models import GoalCategory, Goal, KPI, ProgressUpdate, Milestone, GoalComment
from authentication.models import User


class UserSimpleSerializer(serializers.ModelSerializer):
    """Simple user serializer for nested representations"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class GoalCategorySerializer(serializers.ModelSerializer):
    """Serializer for goal categories"""
    class Meta:
        model = GoalCategory
        fields = ['id', 'name', 'description', 'color', 'created_at']


class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for milestones"""
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Milestone
        fields = ['id', 'goal', 'title', 'description', 'due_date', 'completed_date', 
                  'status', 'order', 'is_overdue', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class GoalCommentSerializer(serializers.ModelSerializer):
    """Serializer for goal comments"""
    user = UserSimpleSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = GoalComment
        fields = ['id', 'goal', 'user', 'comment', 'parent_comment', 
                  'replies', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get nested replies"""
        if obj.replies.exists():
            return GoalCommentSerializer(obj.replies.all(), many=True).data
        return []


class ProgressUpdateSerializer(serializers.ModelSerializer):
    """Serializer for progress updates"""
    updated_by = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = ProgressUpdate
        fields = ['id', 'goal', 'updated_by', 'progress_percentage', 'current_value',
                  'title', 'description', 'challenges', 'help_needed', 'attachment', 'created_at']
        read_only_fields = ['created_at']
    
    def validate_progress_percentage(self, value):
        """Validate progress percentage"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Progress percentage must be between 0 and 100")
        return value


class GoalListSerializer(serializers.ModelSerializer):
    """Simplified serializer for goal lists"""
    owner = UserSimpleSerializer(read_only=True)
    category = GoalCategorySerializer(read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    achievement_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Goal
        fields = ['id', 'title', 'goal_type', 'priority', 'status', 'owner', 'category',
                  'start_date', 'due_date', 'progress_percentage', 'achievement_percentage',
                  'is_overdue', 'days_remaining', 'is_okr', 'created_at']


class GoalDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual goals"""
    owner = UserSimpleSerializer(read_only=True)
    assigned_to = UserSimpleSerializer(many=True, read_only=True)
    created_by = UserSimpleSerializer(read_only=True)
    category = GoalCategorySerializer(read_only=True)
    
    # Computed fields
    is_overdue = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    achievement_percentage = serializers.ReadOnlyField()
    
    # Related data
    milestones = MilestoneSerializer(many=True, read_only=True)
    progress_updates = ProgressUpdateSerializer(many=True, read_only=True)
    key_results = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = ['id', 'title', 'description', 'category', 'goal_type', 'priority',
                  'owner', 'assigned_to', 'created_by', 'start_date', 'due_date', 
                  'completed_date', 'status', 'progress_percentage', 'target_value',
                  'current_value', 'unit', 'achievement_percentage', 'is_okr', 
                  'parent_goal', 'is_overdue', 'days_remaining', 'milestones',
                  'progress_updates', 'key_results', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'progress_percentage']
    
    def get_key_results(self, obj):
        """Get key results if this is an OKR"""
        if obj.is_okr and obj.key_results.exists():
            return GoalListSerializer(obj.key_results.all(), many=True).data
        return []


class GoalCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating goals"""
    assigned_to_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Goal
        fields = ['title', 'description', 'category', 'goal_type', 'priority',
                  'owner', 'assigned_to_ids', 'start_date', 'due_date', 'status',
                  'target_value', 'current_value', 'unit', 'is_okr', 'parent_goal']
    
    def validate(self, data):
        """Validate goal data"""
        if data.get('start_date') and data.get('due_date'):
            if data['start_date'] > data['due_date']:
                raise serializers.ValidationError("Start date must be before due date")
        
        if data.get('target_value') and data['target_value'] <= 0:
            raise serializers.ValidationError("Target value must be greater than 0")
        
        # Validate parent goal for key results
        if data.get('parent_goal'):
            if not data.get('is_okr'):
                raise serializers.ValidationError("Only OKR key results can have a parent goal")
        
        return data
    
    def create(self, validated_data):
        """Create goal with assigned users"""
        assigned_to_ids = validated_data.pop('assigned_to_ids', [])
        goal = Goal.objects.create(**validated_data)
        
        if assigned_to_ids:
            goal.assigned_to.set(assigned_to_ids)
        
        return goal
    
    def update(self, instance, validated_data):
        """Update goal with assigned users"""
        assigned_to_ids = validated_data.pop('assigned_to_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if assigned_to_ids is not None:
            instance.assigned_to.set(assigned_to_ids)
        
        return instance


class KPISerializer(serializers.ModelSerializer):
    """Serializer for KPIs"""
    owner = UserSimpleSerializer(read_only=True)
    category = GoalCategorySerializer(read_only=True)
    achievement_percentage = serializers.ReadOnlyField()
    performance_level = serializers.ReadOnlyField()
    is_on_track = serializers.ReadOnlyField()
    
    class Meta:
        model = KPI
        fields = ['id', 'name', 'description', 'category', 'owner', 'department',
                  'target_value', 'current_value', 'unit', 'frequency',
                  'threshold_low', 'threshold_medium', 'threshold_high',
                  'period_start', 'period_end', 'related_goal', 'is_active',
                  'achievement_percentage', 'performance_level', 'is_on_track',
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate KPI data"""
        if data.get('period_start') and data.get('period_end'):
            if data['period_start'] > data['period_end']:
                raise serializers.ValidationError("Period start must be before period end")
        
        # Validate thresholds
        thresholds = [
            data.get('threshold_low'),
            data.get('threshold_medium'),
            data.get('threshold_high')
        ]
        
        if all(t is not None for t in thresholds):
            if not (thresholds[0] < thresholds[1] < thresholds[2]):
                raise serializers.ValidationError(
                    "Thresholds must be in ascending order: low < medium < high"
                )
        
        return data


class GoalProgressSerializer(serializers.Serializer):
    """Serializer for updating goal progress"""
    progress_percentage = serializers.IntegerField(min_value=0, max_value=100)
    current_value = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    challenges = serializers.CharField(required=False, allow_blank=True)
    help_needed = serializers.BooleanField(default=False)
    attachment = serializers.FileField(required=False)


class KPIUpdateSerializer(serializers.Serializer):
    """Serializer for updating KPI current value"""
    current_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)


class KPIDashboardSerializer(serializers.Serializer):
    """Serializer for KPI dashboard data"""
    total_kpis = serializers.IntegerField()
    active_kpis = serializers.IntegerField()
    on_track = serializers.IntegerField()
    at_risk = serializers.IntegerField()
    excellent_performance = serializers.IntegerField()
    good_performance = serializers.IntegerField()
    average_performance = serializers.IntegerField()
    poor_performance = serializers.IntegerField()
    kpis = KPISerializer(many=True)
