"""
Celery Configuration for Employee Management System
Day 7: Task Notifications & Reminders
"""

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_management.settings')

# Create Celery app
app = Celery('employee_management')

# Load configuration from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'send-task-reminders-every-morning': {
        'task': 'notifications.tasks.send_task_reminders',
        'schedule': crontab(hour=9, minute=0),  # Every day at 9:00 AM
    },
    'check-overdue-tasks-every-hour': {
        'task': 'notifications.tasks.check_overdue_tasks',
        'schedule': crontab(minute=0),  # Every hour
    },
    'escalate-critical-tasks': {
        'task': 'notifications.tasks.escalate_critical_tasks',
        'schedule': crontab(hour='*/2'),  # Every 2 hours
    },
}

@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery configuration."""
    print(f'Request: {self.request!r}')
