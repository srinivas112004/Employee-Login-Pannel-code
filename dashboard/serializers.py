"""
Dashboard App - Serializers
Day 4: Serializers for dashboard APIs.
Day 6: Added Project, Milestone, and FileAttachment serializers.
"""

from rest_framework import serializers
from django.db.models import Count, Q
from django.utils import timezone
from .models import Announcement, Task, LeaveBalance, Project, Milestone, FileAttachment
from authentication.models import User


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for Announcement model."""
    created_by_name = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'content', 'priority', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'is_active', 'expires_at', 'is_expired'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_created_by_name(self, obj):
        """Get creator's full name."""
        return obj.created_by.get_full_name()


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model. Day 6: Added project and subtask support."""
    assigned_to_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    project_name = serializers.SerializerMethodField()
    parent_task_title = serializers.SerializerMethodField()
    subtask_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assigned_to', 'assigned_to_name', 'assigned_by', 'assigned_by_name',
            'project', 'project_name', 'parent_task', 'parent_task_title', 'subtask_count',
            'due_date', 'created_at', 'updated_at', 'completed_at', 'is_overdue'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'assigned_by']
    
    def get_assigned_to_name(self, obj):
        """Get assignee's full name."""
        return obj.assigned_to.get_full_name()
    
    def get_assigned_by_name(self, obj):
        """Get assigner's full name."""
        return obj.assigned_by.get_full_name()
    
    def get_project_name(self, obj):
        """Get project name if task belongs to a project."""
        return obj.project.name if obj.project else None
    
    def get_parent_task_title(self, obj):
        """Get parent task title if this is a subtask."""
        return obj.parent_task.title if obj.parent_task else None
    
    def get_subtask_count(self, obj):
        """Get count of subtasks."""
        return obj.subtasks.count()


class LeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for LeaveBalance model."""
    remaining_days = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    
    class Meta:
        model = LeaveBalance
        fields = [
            'id', 'user', 'leave_type', 'leave_type_display',
            'total_days', 'used_days', 'remaining_days',
            'usage_percentage', 'year'
        ]
        read_only_fields = ['id']


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data."""
    total_employees = serializers.IntegerField()
    active_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    pending_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    recent_announcements = AnnouncementSerializer(many=True)
    my_tasks_summary = serializers.DictField()
    leave_summary = serializers.DictField()


class TaskSummarySerializer(serializers.Serializer):
    """Serializer for task statistics."""
    total_tasks = serializers.IntegerField()
    todo = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    review = serializers.IntegerField()
    completed = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    overdue = serializers.IntegerField()
    by_priority = serializers.DictField()
    recent_tasks = TaskSerializer(many=True)


# ============================================================================
# DAY 6: PROJECT MANAGEMENT SERIALIZERS
# ============================================================================

class MilestoneSerializer(serializers.ModelSerializer):
    """Serializer for Milestone model."""
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'project', 'name', 'description', 'status',
            'due_date', 'completed_at', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project', 'created_at', 'updated_at']


class FileAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for FileAttachment model."""
    uploaded_by_name = serializers.SerializerMethodField()
    file_size_mb = serializers.ReadOnlyField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = FileAttachment
        fields = [
            'id', 'task', 'project', 'file', 'file_url', 'file_name',
            'file_type', 'file_size', 'file_size_mb',
            'uploaded_by', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'file_size', 'file_name', 'file_type']
    
    def get_uploaded_by_name(self, obj):
        """Get uploader's full name."""
        return obj.uploaded_by.get_full_name()
    
    def get_file_url(self, obj):
        """Get full URL for the file."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    manager_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    assigned_to_details = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    progress_percentage = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()
    
    # Statistics
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    total_milestones = serializers.SerializerMethodField()
    completed_milestones = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'status',
            'manager', 'manager_name', 'created_by', 'created_by_name',
            'assigned_to', 'assigned_to_details',
            'start_date', 'deadline', 'is_overdue', 'days_remaining',
            'progress_percentage', 'total_tasks', 'completed_tasks',
            'total_milestones', 'completed_milestones',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_manager_name(self, obj):
        """Get manager's full name."""
        return obj.manager.get_full_name()
    
    def get_created_by_name(self, obj):
        """Get creator's full name."""
        return obj.created_by.get_full_name()
    
    def get_assigned_to_details(self, obj):
        """Get list of assigned employees/interns with details."""
        return [
            {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'role': user.role
            }
            for user in obj.assigned_to.all()
        ]
    
    def get_total_tasks(self, obj):
        """Get total number of tasks in project."""
        return obj.tasks.count()
    
    def get_completed_tasks(self, obj):
        """Get number of completed tasks."""
        return obj.tasks.filter(status='completed').count()
    
    def get_total_milestones(self, obj):
        """Get total number of milestones."""
        return obj.milestones.count()
    
    def get_completed_milestones(self, obj):
        """Get number of completed milestones."""
        return obj.milestones.filter(status='completed').count()


class ProjectDetailSerializer(ProjectSerializer):
    """Extended project serializer with nested tasks, milestones, and attachments."""
    tasks = TaskSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)
    
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['tasks', 'milestones', 'attachments']


class SubtaskSerializer(serializers.ModelSerializer):
    """Simplified serializer for subtasks."""
    assigned_to_name = serializers.SerializerMethodField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'assigned_to', 'assigned_to_name', 'parent_task',
            'due_date', 'is_overdue', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_assigned_to_name(self, obj):
        """Get assignee's full name."""
        return obj.assigned_to.get_full_name()
