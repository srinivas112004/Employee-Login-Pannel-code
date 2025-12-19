"""
Models for Learning Management System (LMS)
Handles courses, modules, enrollments, and progress tracking
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from authentication.models import User


class Course(models.Model):
    """Course model for training and learning"""
    
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical Skills'),
        ('soft_skills', 'Soft Skills'),
        ('leadership', 'Leadership'),
        ('compliance', 'Compliance'),
        ('onboarding', 'Onboarding'),
        ('professional', 'Professional Development'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    instructor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses_taught'
    )
    
    # Course details
    duration_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.5)],
        help_text="Estimated course duration in hours"
    )
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', null=True, blank=True)
    is_mandatory = models.BooleanField(default=False)
    prerequisites = models.TextField(blank=True, help_text="Required knowledge or courses")
    learning_objectives = models.TextField(help_text="What students will learn")
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    max_enrollments = models.PositiveIntegerField(null=True, blank=True)
    enrollment_deadline = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='courses_created'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['is_mandatory']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def total_modules(self):
        """Get total number of modules in course"""
        return self.modules.count()
    
    @property
    def total_enrollments(self):
        """Get total number of enrollments"""
        return self.enrollments.filter(status='active').count()
    
    @property
    def is_full(self):
        """Check if course has reached max enrollment"""
        if not self.max_enrollments:
            return False
        return self.total_enrollments >= self.max_enrollments
    
    @property
    def completion_rate(self):
        """Calculate course completion rate"""
        total = self.enrollments.filter(status='active').count()
        if total == 0:
            return 0
        completed = self.enrollments.filter(status='completed').count()
        return round((completed / total) * 100, 2)


class Module(models.Model):
    """Course module/lesson"""
    
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('document', 'Document'),
        ('quiz', 'Quiz'),
        ('interactive', 'Interactive'),
        ('reading', 'Reading Material'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    description = models.TextField()
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    order = models.PositiveIntegerField(default=0)
    
    # Content
    content = models.TextField(help_text="Module content or instructions")
    video_url = models.URLField(blank=True, null=True)
    document = models.FileField(upload_to='courses/modules/', blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)]
    )
    
    # Settings
    is_mandatory = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['course', 'order']
        unique_together = ['course', 'order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    """Course enrollment tracking"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
        ('expired', 'Expired'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_enrollments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Enrollment details
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    
    # Progress
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    modules_completed = models.PositiveIntegerField(default=0)
    
    # Assessment
    final_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Approval (for mandatory courses)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_enrollments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-enrolled_at']
        unique_together = ['course', 'user']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['course', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.course.title}"
    
    def start_course(self):
        """Mark course as started"""
        if not self.started_at:
            self.started_at = timezone.now()
            self.save()
    
    def complete_course(self):
        """Mark course as completed"""
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.progress_percentage = 100
            self.save()
    
    @property
    def is_overdue(self):
        """Check if enrollment is overdue"""
        if not self.deadline:
            return False
        return timezone.now().date() > self.deadline and self.status not in ['completed', 'dropped']
    
    @property
    def time_spent_days(self):
        """Calculate days spent on course"""
        if not self.started_at:
            return 0
        end_time = self.completed_at or timezone.now()
        return (end_time - self.started_at).days


class ModuleProgress(models.Model):
    """Track individual module progress for each user"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='module_progress'
    )
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(default=0)
    
    # Content tracking
    last_position = models.CharField(
        max_length=255,
        blank=True,
        help_text="Last position in video/document (e.g., '5:30' for video)"
    )
    attempts = models.PositiveIntegerField(default=0)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['enrollment', 'module__order']
        unique_together = ['enrollment', 'module']
        indexes = [
            models.Index(fields=['enrollment', 'status']),
        ]
    
    def __str__(self):
        return f"{self.enrollment.user.get_full_name()} - {self.module.title}"
    
    def mark_started(self):
        """Mark module as started"""
        if self.status == 'not_started':
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.enrollment.start_course()
            self.save()
    
    def mark_completed(self):
        """Mark module as completed"""
        if self.status != 'completed':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            
            # Update enrollment progress
            enrollment = self.enrollment
            enrollment.modules_completed = enrollment.module_progress.filter(
                status='completed'
            ).count()
            
            total_modules = enrollment.course.modules.filter(is_mandatory=True).count()
            if total_modules > 0:
                enrollment.progress_percentage = (
                    enrollment.modules_completed / total_modules
                ) * 100
            
            enrollment.save()
            
            # Check if all modules completed
            if enrollment.modules_completed >= total_modules:
                enrollment.complete_course()


class Quiz(models.Model):
    """Quiz/Assessment model for courses"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='quizzes'
    )
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='quizzes',
        null=True,
        blank=True
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    
    # Quiz settings
    time_limit_minutes = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Time limit in minutes (null = no limit)"
    )
    passing_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=70,
        help_text="Minimum score to pass (percentage)"
    )
    max_attempts = models.PositiveIntegerField(
        default=3,
        help_text="Maximum attempts allowed"
    )
    is_mandatory = models.BooleanField(default=False)
    randomize_questions = models.BooleanField(default=True)
    show_correct_answers = models.BooleanField(
        default=True,
        help_text="Show correct answers after submission"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='quizzes_created'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Quizzes"
        indexes = [
            models.Index(fields=['course', 'is_mandatory']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"
    
    @property
    def total_questions(self):
        """Get total number of questions"""
        return self.questions.count()
    
    @property
    def total_points(self):
        """Get total points available"""
        return self.questions.aggregate(
            total=models.Sum('points')
        )['total'] or 0


class QuizQuestion(models.Model):
    """Individual quiz questions"""
    
    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('text', 'Text Answer'),
    ]
    
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='questions'
    )
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    points = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=1
    )
    order = models.PositiveIntegerField(default=0)
    
    # For multiple choice questions (JSON format)
    # Example: ["Option A", "Option B", "Option C", "Option D"]
    options = models.JSONField(null=True, blank=True)
    
    # Correct answer(s) - stored as JSON
    # Single choice: ["A"] or ["Option A"]
    # Multiple choice: ["A", "C"] or ["Option A", "Option C"]
    # True/False: ["True"] or ["False"]
    # Text: ["correct answer"] (for auto-grading, can be null for manual grading)
    correct_answer = models.JSONField()
    
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after answering"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['quiz', 'order']
        unique_together = [['quiz', 'order']]
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class QuizAttempt(models.Model):
    """Quiz attempt/submission by user"""
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
    ]
    
    quiz = models.ForeignKey(
        Quiz, 
        on_delete=models.CASCADE, 
        related_name='attempts'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='quiz_attempts'
    )
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        null=True,
        blank=True
    )
    
    attempt_number = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    
    # Scoring
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    points_earned = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=0
    )
    total_points = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        default=0
    )
    passed = models.BooleanField(default=False)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    time_taken_minutes = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Answers stored as JSON
    # Format: {"question_id": {"answer": [...], "is_correct": bool, "points": float}}
    answers = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-started_at']
        unique_together = [['quiz', 'user', 'attempt_number']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['quiz', 'passed']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} (Attempt {self.attempt_number})"
    
    def calculate_score(self):
        """Calculate score based on answers"""
        if not self.answers:
            self.score = 0
            self.points_earned = 0
            return
        
        points = sum(
            answer.get('points', 0) 
            for answer in self.answers.values()
        )
        self.points_earned = points
        
        if self.total_points > 0:
            self.score = (points / float(self.total_points)) * 100
        else:
            self.score = 0
        
        self.passed = self.score >= self.quiz.passing_score
        self.save()


class Certificate(models.Model):
    """Certificate issued upon course completion"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='certificates'
    )
    course = models.ForeignKey(
        Course, 
        on_delete=models.CASCADE, 
        related_name='certificates'
    )
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='certificate',
        null=True,
        blank=True
    )
    
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Certificate details
    issued_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Performance metrics
    completion_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Overall course completion score"
    )
    quiz_average = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Average quiz score"
    )
    
    # Certificate file
    certificate_file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True
    )
    
    # Verification
    verification_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issued_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='certificates_issued'
    )
    
    class Meta:
        ordering = ['-issued_date']
        unique_together = [['user', 'course']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['certificate_id']),
        ]
    
    def __str__(self):
        return f"{self.certificate_id} - {self.user.email} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID
            import uuid
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m')
            self.certificate_id = f"CERT-{date_str}-{uuid.uuid4().hex[:8].upper()}"
        
        if not self.title:
            self.title = f"Certificate of Completion: {self.course.title}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if certificate is currently valid"""
        if self.status != 'active':
            return False
        
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        
        return True


class Skill(models.Model):
    """Skills that can be earned from courses"""
    
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('soft_skill', 'Soft Skills'),
        ('leadership', 'Leadership'),
        ('compliance', 'Compliance'),
        ('language', 'Language'),
        ('tool', 'Tool/Software'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Associated courses that teach this skill
    courses = models.ManyToManyField(
        Course,
        related_name='skills_taught',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class UserSkill(models.Model):
    """User's acquired skills with proficiency level"""
    
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    SOURCE_CHOICES = [
        ('course', 'Course Completion'),
        ('assessment', 'Assessment'),
        ('manual', 'Manual Entry'),
        ('endorsement', 'Peer Endorsement'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_skills'
    )
    skill = models.ForeignKey(
        Skill, 
        on_delete=models.CASCADE, 
        related_name='user_proficiencies'
    )
    
    proficiency_level = models.CharField(
        max_length=20, 
        choices=PROFICIENCY_CHOICES,
        default='beginner'
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='course')
    
    # Optional reference to course/certificate
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skill_acquisitions'
    )
    certificate = models.ForeignKey(
        Certificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='skills_earned'
    )
    
    # Endorsements
    endorsement_count = models.PositiveIntegerField(default=0)
    
    acquired_date = models.DateField(auto_now_add=True)
    last_used_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-acquired_date']
        unique_together = [['user', 'skill']]
        indexes = [
            models.Index(fields=['user', 'proficiency_level']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.skill.name} ({self.proficiency_level})"
