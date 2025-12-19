"""
Notifications App - Views
Day 7: Task Notifications & Reminders API endpoints
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from .models import Notification, NotificationPreference, TaskEscalation
from .serializers import (
    NotificationSerializer, NotificationPreferenceSerializer,
    TaskEscalationSerializer, NotificationStatsSerializer
)
from dashboard.models import Task
from .tasks import create_notification


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    Provides CRUD operations and additional actions for notification management.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for current user."""
        user = self.request.user
        
        # Admin can see all notifications, others see only their own
        if user.role == 'admin':
            return Notification.objects.all().select_related('user', 'task', 'project')
        return Notification.objects.filter(user=user).select_related('task', 'project')
    
    def create(self, request, *args, **kwargs):
        """Create notification (admin/manager only)."""
        if request.user.role not in ['admin', 'manager']:
            return Response(
                {'error': 'Only admin and managers can create notifications'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications for current user."""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        return Response({
            'count': unread.count(),
            'notifications': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'message': 'Notification marked as read',
            'notification': self.get_serializer(notification).data
        })
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read for current user."""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'message': f'{updated} notifications marked as read'
        })
    
    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        """Delete all read notifications for current user."""
        deleted_count, _ = self.get_queryset().filter(is_read=True).delete()
        return Response({
            'message': f'{deleted_count} notifications deleted'
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get notification statistics for current user."""
        user = request.user
        notifications = self.get_queryset()
        
        # Calculate stats
        total = notifications.count()
        unread = notifications.filter(is_read=False).count()
        urgent = notifications.filter(priority='urgent', is_read=False).count()
        
        # Get recent notifications (last 10)
        recent = notifications[:10]
        
        # Group by type
        by_type = notifications.values('notification_type').annotate(
            count=Count('id')
        )
        notifications_by_type = {item['notification_type']: item['count'] for item in by_type}
        
        stats_data = {
            'total_notifications': total,
            'unread_notifications': unread,
            'urgent_notifications': urgent,
            'recent_notifications': recent,
            'notifications_by_type': notifications_by_type
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notification preferences.
    Users can customize their notification settings.
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return preference for current user."""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create preferences for current user."""
        obj, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return obj
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's notification preferences."""
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_preferences(self, request):
        """Update current user's notification preferences."""
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Preferences updated successfully',
            'preferences': serializer.data
        })


class TaskEscalationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing task escalations.
    Admin and managers can escalate tasks.
    """
    serializer_class = TaskEscalationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return escalations based on user role."""
        user = self.request.user
        
        if user.role == 'admin':
            # Admin sees all escalations
            return TaskEscalation.objects.all().select_related('task', 'escalated_by', 'escalated_to')
        elif user.role == 'manager':
            # Manager sees escalations assigned to them or created by them
            return TaskEscalation.objects.filter(
                Q(escalated_to=user) | Q(escalated_by=user)
            ).select_related('task', 'escalated_by', 'escalated_to')
        else:
            # Employees see escalations related to their tasks
            return TaskEscalation.objects.filter(
                task__assigned_to=user
            ).select_related('task', 'escalated_by', 'escalated_to')
    
    def create(self, request, *args, **kwargs):
        """Create a task escalation."""
        if request.user.role == 'employee':
            return Response(
                {'error': 'Only managers and admins can escalate tasks'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Add escalated_by to request data
        request.data['escalated_by'] = request.user.id
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        escalation = serializer.save(escalated_by=request.user)
        
        # Send notification
        task = escalation.task
        create_notification.delay(
            user_id=escalation.escalated_to.id,
            notification_type='task_escalated',
            title=f"Task Escalated: {task.title}",
            message=f"Task '{task.title}' has been escalated to you.\nReason: {escalation.get_reason_display()}\nNotes: {escalation.notes}",
            task_id=task.id,
            priority='urgent'
        )
        
        return Response(
            {
                'message': 'Task escalated successfully',
                'escalation': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark an escalation as resolved."""
        escalation = self.get_object()
        
        if request.user not in [escalation.escalated_to, escalation.escalated_by] and request.user.role != 'admin':
            return Response(
                {'error': 'You do not have permission to resolve this escalation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        escalation.resolve()
        
        return Response({
            'message': 'Escalation marked as resolved',
            'escalation': self.get_serializer(escalation).data
        })
    
    @action(detail=False, methods=['get'])
    def unresolved(self, request):
        """Get all unresolved escalations."""
        unresolved = self.get_queryset().filter(is_resolved=False)
        serializer = self.get_serializer(unresolved, many=True)
        return Response({
            'count': unresolved.count(),
            'escalations': serializer.data
        })

