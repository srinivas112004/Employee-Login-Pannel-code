"""
Notifications App - Models
Day 7: Task Notifications & Reminders
"""

from django.db import models
from django.utils import timezone
from authentication.models import User
from dashboard.models import Task, Project


class Notification(models.Model):
    """
    Model for storing user notifications.
    Supports email, in-app, and push notifications.
    """
    TYPE_CHOICES = [
        ('task_assigned', 'Task Assigned'),
        ('task_due_soon', 'Task Due Soon'),
        ('task_overdue', 'Task Overdue'),
        ('task_completed', 'Task Completed'),
        ('task_escalated', 'Task Escalated'),
        ('project_update', 'Project Update'),
        ('milestone_reached', 'Milestone Reached'),
        ('announcement', 'Announcement'),
        ('system', 'System Notification'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects (optional)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    # Notification channels
    sent_email = models.BooleanField(default=False)
    sent_in_app = models.BooleanField(default=True)
    sent_push = models.BooleanField(default=False)
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """
    Model for user notification preferences.
    Users can customize which notifications they want to receive.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_task_assigned = models.BooleanField(default=True)
    email_task_due_soon = models.BooleanField(default=True)
    email_task_overdue = models.BooleanField(default=True)
    email_task_completed = models.BooleanField(default=False)
    email_task_escalated = models.BooleanField(default=True)
    email_project_update = models.BooleanField(default=True)
    email_milestone_reached = models.BooleanField(default=True)
    email_announcement = models.BooleanField(default=True)
    
    # In-app preferences
    inapp_task_assigned = models.BooleanField(default=True)
    inapp_task_due_soon = models.BooleanField(default=True)
    inapp_task_overdue = models.BooleanField(default=True)
    inapp_task_completed = models.BooleanField(default=True)
    inapp_task_escalated = models.BooleanField(default=True)
    inapp_project_update = models.BooleanField(default=True)
    inapp_milestone_reached = models.BooleanField(default=True)
    inapp_announcement = models.BooleanField(default=True)
    
    # General settings
    reminder_hours_before_due = models.IntegerField(default=24, help_text="Hours before due date to send reminder")
    digest_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', 'Real-time'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest'),
            ('never', 'Never'),
        ],
        default='realtime'
    )
    
    quiet_hours_start = models.TimeField(null=True, blank=True, help_text="Start of quiet hours (no notifications)")
    quiet_hours_end = models.TimeField(null=True, blank=True, help_text="End of quiet hours")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.get_full_name()}"
    
    def should_send_email(self, notification_type):
        """Check if email should be sent for this notification type."""
        field_name = f"email_{notification_type}"
        return getattr(self, field_name, False)
    
    def should_send_inapp(self, notification_type):
        """Check if in-app notification should be sent."""
        field_name = f"inapp_{notification_type}"
        return getattr(self, field_name, True)


class TaskEscalation(models.Model):
    """
    Model for tracking task escalations.
    Records when and why tasks were escalated.
    """
    REASON_CHOICES = [
        ('overdue', 'Task Overdue'),
        ('critical_priority', 'Critical Priority'),
        ('blocked', 'Task Blocked'),
        ('manual', 'Manual Escalation'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='escalations')
    escalated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='escalations_created')
    escalated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalations_received')
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'task_escalations'
        verbose_name = 'Task Escalation'
        verbose_name_plural = 'Task Escalations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Escalation: {self.task.title} to {self.escalated_to.get_full_name()}"
    
    def resolve(self):
        """Mark escalation as resolved."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.save(update_fields=['is_resolved', 'resolved_at'])

