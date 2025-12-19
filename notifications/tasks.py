"""
Notifications App - Celery Tasks
Day 7: Async tasks for sending notifications and reminders
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import Notification, NotificationPreference, TaskEscalation
from dashboard.models import Task
from authentication.models import User


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, notification_id):
    """
    Send email notification to user.
    Retries up to 3 times if sending fails.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        user = notification.user
        
        # Check user preferences
        try:
            preferences = user.notification_preferences
            if not preferences.should_send_email(notification.notification_type):
                notification.sent_email = False
                notification.save(update_fields=['sent_email'])
                return f"Email skipped based on user preferences for notification {notification_id}"
        except NotificationPreference.DoesNotExist:
            # If no preferences, send email by default
            pass
        
        # Send email
        subject = f"{settings.EMAIL_SUBJECT_PREFIX}{notification.title}"
        message = notification.message
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        # Update notification status
        notification.sent_email = True
        notification.save(update_fields=['sent_email'])
        
        return f"Email sent successfully for notification {notification_id}"
        
    except Notification.DoesNotExist:
        return f"Notification {notification_id} not found"
    except Exception as exc:
        # Retry on failure
        raise self.retry(exc=exc, countdown=60)  # Retry after 60 seconds


@shared_task
def create_notification(user_id, notification_type, title, message, task_id=None, project_id=None, priority='medium'):
    """
    Create a notification and optionally send email.
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Create notification
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            task_id=task_id,
            project_id=project_id,
            priority=priority,
            sent_in_app=True,
        )
        
        # Send email asynchronously
        send_email_notification.delay(notification.id)
        
        return f"Notification created: {notification.id}"
        
    except User.DoesNotExist:
        return f"User {user_id} not found"
    except Exception as e:
        return f"Error creating notification: {str(e)}"


@shared_task
def send_task_reminders():
    """
    Celery Beat task to send reminders for tasks due soon.
    Runs every morning at 9:00 AM.
    """
    # Get all users with notification preferences
    users = User.objects.filter(is_active=True)
    
    notifications_sent = 0
    
    for user in users:
        try:
            # Get user's reminder preference (default 24 hours)
            try:
                preferences = user.notification_preferences
                reminder_hours = preferences.reminder_hours_before_due
            except NotificationPreference.DoesNotExist:
                reminder_hours = 24
            
            # Calculate reminder window
            now = timezone.now()
            reminder_start = now
            reminder_end = now + timedelta(hours=reminder_hours)
            
            # Find tasks due within reminder window
            tasks_due_soon = Task.objects.filter(
                Q(assigned_to=user) &
                Q(status__in=['todo', 'in_progress']) &
                Q(due_date__gte=reminder_start) &
                Q(due_date__lte=reminder_end)
            )
            
            for task in tasks_due_soon:
                hours_until_due = (task.due_date - now).total_seconds() / 3600
                
                title = f"Task Due Soon: {task.title}"
                message = (
                    f"Your task '{task.title}' is due in {int(hours_until_due)} hours.\n\n"
                    f"Priority: {task.get_priority_display()}\n"
                    f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Please ensure it's completed on time."
                )
                
                create_notification.delay(
                    user_id=user.id,
                    notification_type='task_due_soon',
                    title=title,
                    message=message,
                    task_id=task.id,
                    priority=task.priority
                )
                notifications_sent += 1
                
        except Exception as e:
            print(f"Error sending reminder to user {user.id}: {str(e)}")
            continue
    
    return f"Sent {notifications_sent} task reminders"


@shared_task
def check_overdue_tasks():
    """
    Celery Beat task to check for overdue tasks and send notifications.
    Runs every hour.
    """
    now = timezone.now()
    
    # Find overdue tasks
    overdue_tasks = Task.objects.filter(
        Q(status__in=['todo', 'in_progress']) &
        Q(due_date__lt=now)
    ).select_related('assigned_to', 'assigned_by')
    
    notifications_sent = 0
    
    for task in overdue_tasks:
        # Check if we already sent an overdue notification today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        existing_notification = Notification.objects.filter(
            user=task.assigned_to,
            task=task,
            notification_type='task_overdue',
            created_at__gte=today_start
        ).exists()
        
        if not existing_notification:
            hours_overdue = (now - task.due_date).total_seconds() / 3600
            
            # Notify assigned user
            title = f"Task Overdue: {task.title}"
            message = (
                f"Your task '{task.title}' is overdue by {int(hours_overdue)} hours.\n\n"
                f"Priority: {task.get_priority_display()}\n"
                f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                f"Please complete it as soon as possible."
            )
            
            create_notification.delay(
                user_id=task.assigned_to.id,
                notification_type='task_overdue',
                title=title,
                message=message,
                task_id=task.id,
                priority='urgent'
            )
            
            # Also notify manager
            if task.assigned_by and task.assigned_by != task.assigned_to:
                manager_message = (
                    f"Task '{task.title}' assigned to {task.assigned_to.get_full_name()} is overdue by {int(hours_overdue)} hours.\n\n"
                    f"Priority: {task.get_priority_display()}\n"
                    f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}"
                )
                
                create_notification.delay(
                    user_id=task.assigned_by.id,
                    notification_type='task_overdue',
                    title=f"Team Member's Task Overdue: {task.title}",
                    message=manager_message,
                    task_id=task.id,
                    priority='high'
                )
            
            notifications_sent += 2
    
    return f"Sent {notifications_sent} overdue task notifications"


@shared_task
def escalate_critical_tasks():
    """
    Celery Beat task to escalate critical overdue tasks.
    Runs every 2 hours.
    """
    now = timezone.now()
    escalation_threshold = now - timedelta(hours=48)  # Tasks overdue for 48+ hours
    
    # Find critical overdue tasks
    critical_tasks = Task.objects.filter(
        Q(status__in=['todo', 'in_progress']) &
        Q(priority__in=['high', 'urgent']) &
        Q(due_date__lt=escalation_threshold)
    ).select_related('assigned_to', 'assigned_by', 'project')
    
    escalations_created = 0
    
    for task in critical_tasks:
        # Check if already escalated recently
        recent_escalation = TaskEscalation.objects.filter(
            task=task,
            created_at__gte=now - timedelta(hours=24),
            is_resolved=False
        ).exists()
        
        if not recent_escalation:
            # Find escalation target (task creator's manager or admin)
            escalate_to = task.assigned_by if task.assigned_by else None
            
            if not escalate_to:
                # Escalate to admin
                escalate_to = User.objects.filter(role='admin', is_active=True).first()
            
            if escalate_to:
                # Create escalation record
                escalation = TaskEscalation.objects.create(
                    task=task,
                    escalated_to=escalate_to,
                    reason='overdue',
                    notes=f"Task has been overdue for more than 48 hours"
                )
                
                # Send notification
                hours_overdue = (now - task.due_date).total_seconds() / 3600
                title = f"ESCALATED: Critical Task Overdue - {task.title}"
                message = (
                    f"A critical task has been escalated to you.\n\n"
                    f"Task: {task.title}\n"
                    f"Assigned to: {task.assigned_to.get_full_name()}\n"
                    f"Priority: {task.get_priority_display()}\n"
                    f"Overdue by: {int(hours_overdue)} hours\n"
                    f"Project: {task.project.name if task.project else 'N/A'}\n\n"
                    f"Immediate action required."
                )
                
                create_notification.delay(
                    user_id=escalate_to.id,
                    notification_type='task_escalated',
                    title=title,
                    message=message,
                    task_id=task.id,
                    priority='urgent'
                )
                
                escalations_created += 1
    
    return f"Created {escalations_created} task escalations"


@shared_task
def send_task_assignment_notification(task_id):
    """
    Send notification when a task is assigned.
    """
    try:
        task = Task.objects.select_related('assigned_to', 'assigned_by', 'project').get(id=task_id)
        
        title = f"New Task Assigned: {task.title}"
        message = (
            f"You have been assigned a new task.\n\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Priority: {task.get_priority_display()}\n"
            f"Due Date: {task.due_date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Assigned by: {task.assigned_by.get_full_name() if task.assigned_by else 'System'}\n"
            f"Project: {task.project.name if task.project else 'N/A'}"
        )
        
        create_notification.delay(
            user_id=task.assigned_to.id,
            notification_type='task_assigned',
            title=title,
            message=message,
            task_id=task.id,
            priority=task.priority
        )
        
        return f"Task assignment notification sent for task {task_id}"
        
    except Task.DoesNotExist:
        return f"Task {task_id} not found"
