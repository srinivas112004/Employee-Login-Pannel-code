"""
Admin configuration for Learning Management System (LMS)
"""

from django.contrib import admin
from .models import (
    Course, Module, Enrollment, ModuleProgress,
    Quiz, QuizQuestion, QuizAttempt, Certificate, Skill, UserSkill
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course"""
    
    list_display = [
        'title', 'category', 'level', 'instructor', 'status',
        'is_mandatory', 'duration_hours', 'total_enrollments', 'created_at'
    ]
    list_filter = ['status', 'category', 'level', 'is_mandatory', 'created_at']
    search_fields = ['title', 'description', 'instructor__email']
    readonly_fields = ['created_at', 'updated_at', 'total_modules', 'total_enrollments', 'completion_rate']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'level', 'instructor')
        }),
        ('Course Details', {
            'fields': ('duration_hours', 'thumbnail', 'is_mandatory', 'prerequisites', 'learning_objectives')
        }),
        ('Status & Limits', {
            'fields': ('status', 'max_enrollments', 'enrollment_deadline', 'start_date', 'end_date')
        }),
        ('Statistics', {
            'fields': ('total_modules', 'total_enrollments', 'completion_rate'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin interface for Module"""
    
    list_display = [
        'title', 'course', 'content_type', 'order', 'duration_minutes',
        'is_mandatory', 'is_published', 'created_at'
    ]
    list_filter = ['content_type', 'is_mandatory', 'is_published', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'title', 'description', 'content_type', 'order')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'document', 'duration_minutes')
        }),
        ('Settings', {
            'fields': ('is_mandatory', 'is_published')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admin interface for Enrollment"""
    
    list_display = [
        'user', 'course', 'status', 'progress_percentage', 'modules_completed',
        'enrolled_at', 'completed_at', 'is_overdue'
    ]
    list_filter = ['status', 'enrolled_at', 'completed_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'course__title']
    readonly_fields = ['enrolled_at', 'updated_at', 'is_overdue', 'time_spent_days']
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('course', 'user', 'status', 'deadline')
        }),
        ('Progress', {
            'fields': ('progress_percentage', 'modules_completed', 'final_score',
                      'started_at', 'completed_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('is_overdue', 'time_spent_days'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('enrolled_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    """Admin interface for ModuleProgress"""
    
    list_display = [
        'enrollment', 'module', 'status', 'time_spent_minutes',
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'started_at', 'completed_at']
    search_fields = [
        'enrollment__user__email', 'enrollment__user__first_name',
        'enrollment__user__last_name', 'module__title'
    ]
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Progress Details', {
            'fields': ('enrollment', 'module', 'status')
        }),
        ('Tracking', {
            'fields': ('started_at', 'completed_at', 'time_spent_minutes',
                      'last_position', 'attempts')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================================================
# DAY 21 ADMIN - Quiz, Certificate, Skills
# ============================================================================

class QuizQuestionInline(admin.TabularInline):
    """Inline for quiz questions"""
    model = QuizQuestion
    extra = 1
    fields = ['order', 'question_text', 'question_type', 'points', 'options', 'correct_answer']


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin interface for Quiz"""
    
    list_display = [
        'title', 'course', 'module', 'difficulty', 'passing_score',
        'max_attempts', 'is_mandatory', 'total_questions', 'created_at'
    ]
    list_filter = ['difficulty', 'is_mandatory', 'created_at']
    search_fields = ['title', 'description', 'course__title']
    readonly_fields = ['created_at', 'updated_at', 'total_questions', 'total_points']
    inlines = [QuizQuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('course', 'module', 'title', 'description', 'difficulty')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit_minutes', 'passing_score', 'max_attempts',
                      'is_mandatory', 'randomize_questions', 'show_correct_answers')
        }),
        ('Statistics', {
            'fields': ('total_questions', 'total_points'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    """Admin interface for QuizQuestion"""
    
    list_display = ['quiz', 'order', 'question_text_short', 'question_type', 'points', 'created_at']
    list_filter = ['question_type', 'created_at']
    search_fields = ['question_text', 'quiz__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'order', 'question_text', 'question_type', 'points')
        }),
        ('Answer Options', {
            'fields': ('options', 'correct_answer', 'explanation')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_short(self, obj):
        """Show shortened question text"""
        return obj.question_text[:50] + '...' if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    """Admin interface for QuizAttempt"""
    
    list_display = [
        'user', 'quiz', 'attempt_number', 'status', 'score',
        'passed', 'started_at', 'submitted_at'
    ]
    list_filter = ['status', 'passed', 'started_at', 'submitted_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'quiz__title']
    readonly_fields = ['started_at', 'submitted_at', 'score', 'points_earned', 'total_points', 'passed']
    
    fieldsets = (
        ('Attempt Details', {
            'fields': ('quiz', 'user', 'enrollment', 'attempt_number', 'status')
        }),
        ('Scoring', {
            'fields': ('score', 'points_earned', 'total_points', 'passed')
        }),
        ('Timing', {
            'fields': ('started_at', 'submitted_at', 'time_taken_minutes')
        }),
        ('Answers', {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    """Admin interface for Certificate"""
    
    list_display = [
        'certificate_id', 'user', 'course', 'status', 'issued_date',
        'expiry_date', 'completion_score', 'is_valid'
    ]
    list_filter = ['status', 'issued_date', 'expiry_date']
    search_fields = [
        'certificate_id', 'user__email', 'user__first_name',
        'user__last_name', 'course__title'
    ]
    readonly_fields = ['certificate_id', 'issued_date', 'created_at', 'updated_at', 'is_valid']
    
    fieldsets = (
        ('Certificate Details', {
            'fields': ('certificate_id', 'user', 'course', 'enrollment', 'title', 'description')
        }),
        ('Status', {
            'fields': ('status', 'issued_date', 'expiry_date', 'is_valid')
        }),
        ('Performance', {
            'fields': ('completion_score', 'quiz_average')
        }),
        ('Files & Verification', {
            'fields': ('certificate_file', 'verification_url')
        }),
        ('Metadata', {
            'fields': ('issued_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set issued_by on creation"""
        if not change:
            obj.issued_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin interface for Skill"""
    
    list_display = ['name', 'category', 'courses_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['courses']
    
    fieldsets = (
        ('Skill Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Associated Courses', {
            'fields': ('courses',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def courses_count(self, obj):
        """Show number of courses teaching this skill"""
        return obj.courses.count()
    courses_count.short_description = 'Courses'


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    """Admin interface for UserSkill"""
    
    list_display = [
        'user', 'skill', 'proficiency_level', 'source',
        'endorsement_count', 'acquired_date', 'last_used_date'
    ]
    list_filter = ['proficiency_level', 'source', 'acquired_date']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'skill__name'
    ]
    readonly_fields = ['acquired_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User Skill Details', {
            'fields': ('user', 'skill', 'proficiency_level', 'source')
        }),
        ('Source Information', {
            'fields': ('course', 'certificate')
        }),
        ('Engagement', {
            'fields': ('endorsement_count', 'acquired_date', 'last_used_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
