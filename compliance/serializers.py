"""
Serializers for Compliance and Policy Management
"""

from rest_framework import serializers
from .models import PolicyCategory, Policy, PolicyAcknowledgment, ComplianceReminder
from django.contrib.auth import get_user_model

User = get_user_model()


class PolicyCategorySerializer(serializers.ModelSerializer):
    """Serializer for policy categories"""
    policy_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PolicyCategory
        fields = ['id', 'name', 'description', 'icon', 'policy_count', 'created_at']
        read_only_fields = ['created_at']
    
    def get_policy_count(self, obj):
        return obj.policies.filter(status='published').count()


class PolicyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for policy listings"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    acknowledgment_status = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'version', 'summary', 'status', 'priority',
            'category', 'category_name', 'is_mandatory', 'effective_date',
            'expiry_date', 'requires_signature', 'acknowledgment_deadline_days',
            'created_by_name', 'published_at', 'acknowledgment_status',
            'is_overdue', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'published_at']
    
    def get_acknowledgment_status(self, obj):
        """Get current user's acknowledgment status"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            ack = obj.acknowledgments.get(user=request.user)
            return {
                'acknowledged': ack.acknowledged,
                'acknowledged_at': ack.acknowledged_at
            }
        except PolicyAcknowledgment.DoesNotExist:
            return {'acknowledged': False, 'acknowledged_at': None}
    
    def get_is_overdue(self, obj):
        """Check if acknowledgment is overdue"""
        from datetime import datetime, timedelta
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or obj.status != 'published':
            return False
        
        try:
            ack = obj.acknowledgments.get(user=request.user)
            if ack.acknowledged:
                return False
        except PolicyAcknowledgment.DoesNotExist:
            pass
        
        if obj.published_at:
            deadline = obj.published_at + timedelta(days=obj.acknowledgment_deadline_days)
            return datetime.now(deadline.tzinfo) > deadline
        return False


class PolicyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single policy view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    published_by_name = serializers.CharField(source='published_by.get_full_name', read_only=True, allow_null=True)
    
    acknowledgment_count = serializers.IntegerField(read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    
    user_acknowledgment = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'category', 'category_name', 'version', 'content',
            'summary', 'status', 'priority', 'is_mandatory', 'applies_to_roles',
            'effective_date', 'expiry_date', 'requires_signature',
            'acknowledgment_deadline_days', 'attachment', 'created_by',
            'created_by_name', 'published_by', 'published_by_name', 'published_at',
            'acknowledgment_count', 'pending_count', 'user_acknowledgment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'published_by', 'published_at', 'created_at', 'updated_at']
    
    def get_user_acknowledgment(self, obj):
        """Get current user's full acknowledgment details"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            ack = obj.acknowledgments.get(user=request.user)
            return {
                'acknowledged': ack.acknowledged,
                'acknowledged_at': ack.acknowledged_at,
                'comments': ack.comments,
                'ip_address': ack.ip_address
            }
        except PolicyAcknowledgment.DoesNotExist:
            return None


class PolicyCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating policies"""
    
    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'category', 'version', 'content', 'summary', 'status',
            'priority', 'is_mandatory', 'applies_to_roles', 'effective_date',
            'expiry_date', 'requires_signature', 'acknowledgment_deadline_days',
            'attachment'
        ]
        read_only_fields = ['id']
    
    def validate_applies_to_roles(self, value):
        """Validate role list"""
        if value:
            valid_roles = ['admin', 'hr', 'manager', 'employee', 'intern']
            for role in value:
                if role not in valid_roles:
                    raise serializers.ValidationError(f"Invalid role: {role}")
        return value
    
    def create(self, validated_data):
        """Set created_by on creation"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class PolicyAcknowledgmentSerializer(serializers.ModelSerializer):
    """Serializer for policy acknowledgments"""
    policy_title = serializers.CharField(source='policy.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = PolicyAcknowledgment
        fields = [
            'id', 'policy', 'policy_title', 'user', 'user_name', 'user_email',
            'acknowledged', 'acknowledged_at', 'signature', 'comments',
            'ip_address', 'user_agent', 'created_at', 'updated_at'
        ]
        read_only_fields = ['acknowledged_at', 'ip_address', 'user_agent', 'created_at', 'updated_at']


class AcknowledgeRequestSerializer(serializers.Serializer):
    """Serializer for acknowledgment request"""
    signature = serializers.CharField(required=False, allow_blank=True)
    comments = serializers.CharField(required=False, allow_blank=True)


class ComplianceStatusSerializer(serializers.Serializer):
    """Serializer for compliance status overview"""
    total_policies = serializers.IntegerField()
    acknowledged_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    overdue_count = serializers.IntegerField()
    compliance_percentage = serializers.FloatField()
    pending_policies = PolicyListSerializer(many=True)


class UserComplianceReportSerializer(serializers.Serializer):
    """Serializer for user compliance reports"""
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_email = serializers.EmailField()
    role = serializers.CharField()
    total_policies = serializers.IntegerField()
    acknowledged = serializers.IntegerField()
    pending = serializers.IntegerField()
    overdue = serializers.IntegerField()
    compliance_percentage = serializers.FloatField()
