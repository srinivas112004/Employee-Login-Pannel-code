"""
Notifications App - Serializers
Day 7: Task Notifications & Reminders
"""

from rest_framework import serializers
from .models import Notification, NotificationPreference, TaskEscalation
from authentication.models import User


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    user_name = serializers.SerializerMethodField()
    task_title = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'user_name', 'notification_type', 'notification_type_display',
            'priority', 'priority_display', 'title', 'message',
            'task', 'task_title', 'project', 'project_name',
            'sent_email', 'sent_in_app', 'sent_push',
            'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'sent_email', 'sent_in_app', 'sent_push', 'created_at']
    
    def get_user_name(self, obj):
        """Get user's full name."""
        return obj.user.get_full_name()
    
    def get_task_title(self, obj):
        """Get task title if notification is related to a task."""
        return obj.task.title if obj.task else None
    
    def get_project_name(self, obj):
        """Get project name if notification is related to a project."""
        return obj.project.name if obj.project else None


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for NotificationPreference model."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'user',
            # Email preferences
            'email_task_assigned', 'email_task_due_soon', 'email_task_overdue',
            'email_task_completed', 'email_task_escalated', 'email_project_update',
            'email_milestone_reached', 'email_announcement',
            # In-app preferences
            'inapp_task_assigned', 'inapp_task_due_soon', 'inapp_task_overdue',
            'inapp_task_completed', 'inapp_task_escalated', 'inapp_project_update',
            'inapp_milestone_reached', 'inapp_announcement',
            # General settings
            'reminder_hours_before_due', 'digest_frequency',
            'quiet_hours_start', 'quiet_hours_end',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class TaskEscalationSerializer(serializers.ModelSerializer):
    """Serializer for TaskEscalation model."""
    task_title = serializers.SerializerMethodField()
    escalated_by_name = serializers.SerializerMethodField()
    escalated_to_name = serializers.SerializerMethodField()
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    
    class Meta:
        model = TaskEscalation
        fields = [
            'id', 'task', 'task_title',
            'escalated_by', 'escalated_by_name',
            'escalated_to', 'escalated_to_name',
            'reason', 'reason_display', 'notes',
            'created_at', 'resolved_at', 'is_resolved'
        ]
        read_only_fields = ['id', 'escalated_by', 'created_at']
    
    def get_task_title(self, obj):
        """Get task title."""
        return obj.task.title
    
    def get_escalated_by_name(self, obj):
        """Get escalator's name."""
        return obj.escalated_by.get_full_name() if obj.escalated_by else 'System'
    
    def get_escalated_to_name(self, obj):
        """Get escalation recipient's name."""
        return obj.escalated_to.get_full_name()


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics."""
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    urgent_notifications = serializers.IntegerField()
    recent_notifications = NotificationSerializer(many=True)
    notifications_by_type = serializers.DictField()
