"""
Dashboard App - Models
Day 4: Employee Dashboard features including announcements, tasks, and leave tracking.
Day 6: Added Project, Milestone, Subtask, and File Attachment models.
"""

from django.db import models
from django.utils import timezone
from authentication.models import User


class Announcement(models.Model):
    """
    Model for company-wide announcements.
    Admins/Managers can create announcements visible to all employees.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'announcements'
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.priority}"
    
    @property
    def is_expired(self):
        """Check if announcement has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class Task(models.Model):
    """
    Model for task management.
    Tasks can be assigned to employees by managers.
    Day 6: Added project and parent_task for subtask hierarchy.
    """
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'In Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_assigned')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks_created')
    
    # Day 6: Link tasks to projects and enable subtask hierarchy
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks')
    
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.assigned_to.get_full_name()}"
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False


class LeaveBalance(models.Model):
    """
    Model for tracking employee leave balances.
    Each employee has annual leave quotas.
    """
    LEAVE_TYPE_CHOICES = [
        ('annual', 'Annual Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    total_days = models.DecimalField(max_digits=5, decimal_places=1)  # e.g., 20.0 days
    used_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    year = models.IntegerField(default=timezone.now().year)
    
    class Meta:
        db_table = 'leave_balances'
        verbose_name = 'Leave Balance'
        verbose_name_plural = 'Leave Balances'
        unique_together = [['user', 'leave_type', 'year']]
        ordering = ['user', 'leave_type']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.leave_type}: {self.remaining_days}/{self.total_days}"
    
    @property
    def remaining_days(self):
        """Calculate remaining leave days."""
        return float(self.total_days) - float(self.used_days)
    
    @property
    def usage_percentage(self):
        """Calculate percentage of leave used."""
        if self.total_days > 0:
            return (float(self.used_days) / float(self.total_days)) * 100
        return 0


# ============================================================================
# DAY 6: PROJECT MANAGEMENT MODELS
# ============================================================================

class Project(models.Model):
    """
    Model for organizing tasks into projects.
    Projects group related tasks and track overall progress.
    """
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projects')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    assigned_to = models.ManyToManyField(User, related_name='assigned_projects', blank=True, help_text='Employees/Interns assigned to this project')
    
    start_date = models.DateField()
    deadline = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.manager.get_full_name()}"
    
    @property
    def is_overdue(self):
        """Check if project deadline has passed."""
        if self.status not in ['completed', 'cancelled']:
            return timezone.now().date() > self.deadline
        return False
    
    @property
    def progress_percentage(self):
        """Calculate project completion percentage based on tasks."""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return int((completed_tasks / total_tasks) * 100)
    
    @property
    def days_remaining(self):
        """Calculate days until deadline."""
        if self.status in ['completed', 'cancelled']:
            return 0
        delta = self.deadline - timezone.now().date()
        return max(0, delta.days)


class Milestone(models.Model):
    """
    Model for project milestones.
    Milestones mark important checkpoints in a project.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'milestones'
        verbose_name = 'Milestone'
        verbose_name_plural = 'Milestones'
        ordering = ['due_date']
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    @property
    def is_overdue(self):
        """Check if milestone is overdue."""
        if self.status != 'completed':
            return timezone.now().date() > self.due_date
        return False


class FileAttachment(models.Model):
    """
    Model for file attachments on tasks and projects.
    Supports uploading documents, images, and other files.
    """
    FILE_TYPE_CHOICES = [
        ('document', 'Document'),
        ('image', 'Image'),
        ('spreadsheet', 'Spreadsheet'),
        ('other', 'Other'),
    ]
    
    # Can attach to either task or project
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other')
    file_size = models.BigIntegerField(help_text="File size in bytes")
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file_attachments'
        verbose_name = 'File Attachment'
        verbose_name_plural = 'File Attachments'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        if self.task:
            return f"{self.file_name} - Task: {self.task.title}"
        elif self.project:
            return f"{self.file_name} - Project: {self.project.name}"
        return self.file_name
    
    @property
    def file_size_mb(self):
        """Return file size in megabytes."""
        return round(self.file_size / (1024 * 1024), 2)
