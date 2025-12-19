"""
Performance Management Models - Day 18
Goals, OKRs, KPIs, and Progress Tracking
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from authentication.models import User


class GoalCategory(models.Model):
    """Categories for goals (e.g., Sales, Development, Operations)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Goal Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Goal(models.Model):
    """Goals and OKRs (Objectives and Key Results)"""
    
    GOAL_TYPE_CHOICES = [
        ('individual', 'Individual Goal'),
        ('team', 'Team Goal'),
        ('department', 'Department Goal'),
        ('company', 'Company Goal'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(GoalCategory, on_delete=models.SET_NULL, null=True, related_name='goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPE_CHOICES, default='individual')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_goals', help_text="Primary owner of the goal")
    assigned_to = models.ManyToManyField(User, related_name='assigned_goals', blank=True, help_text="Team members assigned to this goal")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_goals')
    
    # Timeline
    start_date = models.DateField()
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Progress Tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    progress_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall progress percentage (0-100)"
    )
    
    # Target and Achievement
    target_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Target value (e.g., revenue, units, etc.)")
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Current achieved value")
    unit = models.CharField(max_length=50, blank=True, help_text="Unit of measurement (e.g., USD, units, hours)")
    
    # Metadata
    is_okr = models.BooleanField(default=False, help_text="Is this an OKR (Objective and Key Results)?")
    parent_goal = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='key_results', help_text="Parent objective (for key results)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['goal_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.owner.email})"
    
    @property
    def is_overdue(self):
        """Check if goal is overdue"""
        if self.status in ['completed', 'cancelled']:
            return False
        return self.due_date < timezone.now().date()
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        if self.status in ['completed', 'cancelled']:
            return 0
        delta = self.due_date - timezone.now().date()
        return max(0, delta.days)
    
    @property
    def achievement_percentage(self):
        """Calculate achievement based on target and current value"""
        if not self.target_value or self.target_value == 0:
            return self.progress_percentage
        return min(100, int((self.current_value / self.target_value) * 100))
    
    def update_progress(self):
        """Auto-update progress based on key results if it's an OKR"""
        if self.is_okr and self.key_results.exists():
            # Calculate average progress of all key results
            key_results = self.key_results.filter(status__in=['active', 'on_track', 'at_risk', 'completed'])
            if key_results.exists():
                avg_progress = key_results.aggregate(models.Avg('progress_percentage'))['progress_percentage__avg']
                self.progress_percentage = int(avg_progress) if avg_progress else 0
                
                # Update status based on progress
                if self.progress_percentage == 100:
                    self.status = 'completed'
                elif self.progress_percentage >= 75:
                    self.status = 'on_track'
                elif self.progress_percentage >= 50:
                    self.status = 'active'
                else:
                    self.status = 'at_risk'
                
                self.save(update_fields=['progress_percentage', 'status', 'updated_at'])


class KPI(models.Model):
    """Key Performance Indicators"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(GoalCategory, on_delete=models.SET_NULL, null=True, related_name='kpis')
    
    # Assignment
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kpis')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_kpis')
    department = models.CharField(max_length=100, blank=True)
    
    # Measurement
    target_value = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, help_text="Unit of measurement")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    
    # Thresholds
    threshold_low = models.DecimalField(max_digits=12, decimal_places=2, help_text="Below this is poor performance")
    threshold_medium = models.DecimalField(max_digits=12, decimal_places=2, help_text="Above this is good performance")
    threshold_high = models.DecimalField(max_digits=12, decimal_places=2, help_text="Above this is excellent performance")
    
    # Timeline
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Related Goal (optional)
    related_goal = models.ForeignKey(Goal, on_delete=models.SET_NULL, null=True, blank=True, related_name='kpis')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "KPI"
        verbose_name_plural = "KPIs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['period_end']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.owner.email}"
    
    @property
    def achievement_percentage(self):
        """Calculate achievement percentage"""
        if not self.target_value or self.target_value == 0:
            return 0
        return min(100, int((self.current_value / self.target_value) * 100))
    
    @property
    def performance_level(self):
        """Determine performance level based on current value"""
        if self.current_value >= self.threshold_high:
            return 'excellent'
        elif self.current_value >= self.threshold_medium:
            return 'good'
        elif self.current_value >= self.threshold_low:
            return 'average'
        else:
            return 'poor'
    
    @property
    def is_on_track(self):
        """Check if KPI is on track to meet target"""
        return self.current_value >= self.threshold_medium


class ProgressUpdate(models.Model):
    """Progress updates for goals"""
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='progress_updates')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_updates')
    
    # Progress Details
    progress_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Progress percentage at this update"
    )
    current_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Current achieved value")
    
    # Update Content
    title = models.CharField(max_length=255, help_text="Brief title of the update")
    description = models.TextField(help_text="Detailed description of progress")
    
    # Challenges and Blockers
    challenges = models.TextField(blank=True, help_text="Any challenges or blockers faced")
    help_needed = models.BooleanField(default=False, help_text="Does this goal need help?")
    
    # Attachments
    attachment = models.FileField(upload_to='performance/progress/', null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['goal', 'created_at']),
        ]
    
    def __str__(self):
        return f"Progress Update for {self.goal.title} - {self.created_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Update goal progress when saving progress update"""
        super().save(*args, **kwargs)
        
        # Update the goal's progress
        self.goal.progress_percentage = self.progress_percentage
        if self.current_value is not None:
            self.goal.current_value = self.current_value
        
        # Update goal status based on progress
        if self.progress_percentage == 100:
            self.goal.status = 'completed'
            self.goal.completed_date = timezone.now().date()
        elif self.progress_percentage >= 75:
            self.goal.status = 'on_track'
        elif self.progress_percentage >= 50:
            self.goal.status = 'active'
        else:
            self.goal.status = 'at_risk'
        
        self.goal.save(update_fields=['progress_percentage', 'current_value', 'status', 'completed_date', 'updated_at'])


class Milestone(models.Model):
    """Milestones for goals"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
    ]
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='milestones')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_milestones')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Timeline
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Order
    order = models.IntegerField(default=0, help_text="Display order")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'due_date']
        indexes = [
            models.Index(fields=['goal', 'status']),
        ]
    
    def __str__(self):
        return f"{self.goal.title} - {self.title}"
    
    @property
    def is_overdue(self):
        """Check if milestone is overdue"""
        if self.status == 'completed':
            return False
        return self.due_date < timezone.now().date()


class GoalComment(models.Model):
    """Comments and discussions on goals"""
    
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goal_comments')
    comment = models.TextField()
    
    # Reply to another comment
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.goal.title}"
