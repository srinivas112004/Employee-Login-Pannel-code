"""
Models for Performance Reviews & Feedback - Day 19
Review cycles, self-assessment, manager reviews, peer feedback
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from authentication.models import User


class ReviewCycle(models.Model):
    """
    Performance review cycle/period
    Defines when reviews should be conducted
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    REVIEW_TYPE_CHOICES = [
        ('annual', 'Annual Review'),
        ('semi_annual', 'Semi-Annual Review'),
        ('quarterly', 'Quarterly Review'),
        ('probation', 'Probation Review'),
    ]
    
    name = models.CharField(max_length=200, help_text="e.g., 'Q4 2025 Performance Review'")
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPE_CHOICES, default='quarterly')
    description = models.TextField(blank=True)
    
    # Timeline
    start_date = models.DateField(help_text="Review period start date")
    end_date = models.DateField(help_text="Review period end date")
    self_review_deadline = models.DateField(help_text="Deadline for self-assessment")
    manager_review_deadline = models.DateField(help_text="Deadline for manager reviews")
    peer_review_deadline = models.DateField(null=True, blank=True, help_text="Optional peer review deadline")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Participants
    participants = models.ManyToManyField(User, related_name='review_cycles', 
                                         help_text="Employees included in this review cycle")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_review_cycles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['self_review_deadline']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_review_type_display()})"
    
    @property
    def is_self_review_open(self):
        """Check if self-review submission is still open"""
        return self.status == 'active' and timezone.now().date() <= self.self_review_deadline
    
    @property
    def is_manager_review_open(self):
        """Check if manager review submission is still open"""
        return self.status == 'active' and timezone.now().date() <= self.manager_review_deadline
    
    @property
    def is_peer_review_open(self):
        """Check if peer review submission is still open"""
        if not self.peer_review_deadline:
            return False
        return self.status == 'active' and timezone.now().date() <= self.peer_review_deadline


class Review(models.Model):
    """
    Main performance review record
    Aggregates self, manager, and peer reviews
    """
    STATUS_CHOICES = [
        ('pending_self', 'Pending Self-Assessment'),
        ('pending_manager', 'Pending Manager Review'),
        ('pending_peer', 'Pending Peer Feedback'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('draft', 'Draft'),
    ]
    
    cycle = models.ForeignKey(ReviewCycle, on_delete=models.CASCADE, related_name='reviews')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_reviews')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reviews_given',
                                help_text="Manager/Reviewer assigned")
    
    # Overall ratings (calculated from sub-reviews)
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True,
                                        validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_self')
    
    # Final outcome
    promotion_recommended = models.BooleanField(default=False)
    salary_increase_recommended = models.BooleanField(default=False)
    improvement_plan_required = models.BooleanField(default=False)
    
    # Metadata
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['cycle', 'employee']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['cycle', 'status']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.cycle.name}"
    
    def calculate_overall_rating(self):
        """Calculate overall rating from all sub-reviews"""
        ratings = []
        
        if hasattr(self, 'self_assessment') and self.self_assessment.overall_rating:
            ratings.append(float(self.self_assessment.overall_rating))
        
        if hasattr(self, 'manager_review') and self.manager_review.overall_rating:
            ratings.append(float(self.manager_review.overall_rating) * 2)  # Manager review weighted 2x
        
        peer_reviews = self.peer_feedbacks.filter(overall_rating__isnull=False)
        if peer_reviews.exists():
            peer_avg = sum(float(p.overall_rating) for p in peer_reviews) / peer_reviews.count()
            ratings.append(peer_avg)
        
        if ratings:
            self.overall_rating = sum(ratings) / len(ratings)
            self.save()
            return self.overall_rating
        return None


class SelfAssessment(models.Model):
    """
    Employee's self-assessment/self-review
    """
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='self_assessment')
    
    # Key accomplishments
    accomplishments = models.TextField(help_text="Key achievements during review period")
    challenges_faced = models.TextField(blank=True, help_text="Challenges encountered")
    skills_developed = models.TextField(blank=True, help_text="New skills learned")
    
    # Self-ratings (1-5 scale)
    quality_of_work = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    productivity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    initiative = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Goals
    goals_achieved = models.TextField(help_text="Goals achieved from previous review")
    goals_for_next_period = models.TextField(help_text="Goals for next review period")
    
    # Overall
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2,
                                        validators=[MinValueValidator(1), MaxValueValidator(5)])
    additional_comments = models.TextField(blank=True)
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Self-Assessment: {self.review.employee.get_full_name()}"


class ManagerReview(models.Model):
    """
    Manager's review of employee performance
    """
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='manager_review')
    
    # Performance evaluation
    performance_summary = models.TextField(help_text="Overall performance summary")
    strengths = models.TextField(help_text="Employee strengths")
    areas_for_improvement = models.TextField(help_text="Areas needing improvement")
    
    # Manager ratings (1-5 scale)
    quality_of_work = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    productivity = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    initiative = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    leadership = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    problem_solving = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Goals evaluation
    goals_achievement_comment = models.TextField(help_text="Comment on goal achievement")
    goals_for_next_period = models.TextField(help_text="Goals set for next period")
    
    # Recommendations
    promotion_recommendation = models.BooleanField(default=False)
    salary_increase_recommendation = models.BooleanField(default=False)
    training_recommendations = models.TextField(blank=True, help_text="Recommended training/development")
    
    # Overall
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2,
                                        validators=[MinValueValidator(1), MaxValueValidator(5)])
    manager_comments = models.TextField(blank=True, help_text="Additional manager comments")
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Manager Review: {self.review.employee.get_full_name()}"


class PeerFeedback(models.Model):
    """
    Peer feedback/360-degree feedback
    Optional feedback from colleagues
    """
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='peer_feedbacks')
    peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='peer_feedback_given',
                            help_text="Colleague providing feedback")
    
    # Feedback
    collaboration_feedback = models.TextField(help_text="Feedback on collaboration")
    strengths = models.TextField(help_text="Observed strengths")
    areas_for_improvement = models.TextField(blank=True, help_text="Suggested improvements")
    
    # Peer ratings (1-5 scale)
    teamwork = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    communication = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    reliability = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    helpfulness = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    
    # Overall
    overall_rating = models.DecimalField(max_digits=3, decimal_places=2,
                                        validators=[MinValueValidator(1), MaxValueValidator(5)])
    additional_comments = models.TextField(blank=True)
    
    # Confidentiality
    is_anonymous = models.BooleanField(default=True, help_text="Hide peer identity from employee")
    
    # Metadata
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['review', 'peer']
    
    def __str__(self):
        peer_name = "Anonymous" if self.is_anonymous else self.peer.get_full_name()
        return f"Peer Feedback from {peer_name} for {self.review.employee.get_full_name()}"
