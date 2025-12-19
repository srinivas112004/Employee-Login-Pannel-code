"""
Admin interface for Performance Reviews & Feedback - Day 19
"""

from django.contrib import admin
from .models import ReviewCycle, Review, SelfAssessment, ManagerReview, PeerFeedback


@admin.register(ReviewCycle)
class ReviewCycleAdmin(admin.ModelAdmin):
    list_display = ['name', 'review_type', 'status', 'start_date', 'end_date', 'created_by', 'created_at']
    list_filter = ['status', 'review_type', 'start_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'review_type', 'description', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'self_review_deadline', 
                      'manager_review_deadline', 'peer_review_deadline')
        }),
        ('Participants', {
            'fields': ('participants',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['employee', 'cycle', 'reviewer', 'status', 'overall_rating', 'created_at']
    list_filter = ['status', 'cycle', 'promotion_recommended', 'salary_increase_recommended']
    search_fields = ['employee__username', 'employee__first_name', 'employee__last_name']
    readonly_fields = ['overall_rating', 'completed_at', 'created_at', 'updated_at']
    fieldsets = (
        ('Review Information', {
            'fields': ('cycle', 'employee', 'reviewer')
        }),
        ('Status & Ratings', {
            'fields': ('status', 'overall_rating')
        }),
        ('Recommendations', {
            'fields': ('promotion_recommended', 'salary_increase_recommended', 'improvement_plan_required')
        }),
        ('Metadata', {
            'fields': ('completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SelfAssessment)
class SelfAssessmentAdmin(admin.ModelAdmin):
    list_display = ['review', 'get_employee_name', 'overall_rating', 'submitted_at']
    list_filter = ['submitted_at', 'review__cycle']
    search_fields = ['review__employee__username', 'review__employee__first_name']
    readonly_fields = ['submitted_at', 'updated_at']
    fieldsets = (
        ('Review', {
            'fields': ('review',)
        }),
        ('Accomplishments', {
            'fields': ('accomplishments', 'challenges_faced', 'skills_developed')
        }),
        ('Self-Ratings', {
            'fields': ('quality_of_work', 'productivity', 'communication', 'teamwork', 'initiative')
        }),
        ('Goals', {
            'fields': ('goals_achieved', 'goals_for_next_period')
        }),
        ('Overall', {
            'fields': ('overall_rating', 'additional_comments')
        }),
        ('Metadata', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_employee_name(self, obj):
        return obj.review.employee.get_full_name()
    get_employee_name.short_description = 'Employee'


@admin.register(ManagerReview)
class ManagerReviewAdmin(admin.ModelAdmin):
    list_display = ['review', 'get_employee_name', 'overall_rating', 'promotion_recommendation', 'submitted_at']
    list_filter = ['submitted_at', 'review__cycle', 'promotion_recommendation', 'salary_increase_recommendation']
    search_fields = ['review__employee__username', 'review__employee__first_name']
    readonly_fields = ['submitted_at', 'updated_at']
    fieldsets = (
        ('Review', {
            'fields': ('review',)
        }),
        ('Performance Evaluation', {
            'fields': ('performance_summary', 'strengths', 'areas_for_improvement')
        }),
        ('Manager Ratings', {
            'fields': ('quality_of_work', 'productivity', 'communication', 'teamwork', 
                      'initiative', 'leadership', 'problem_solving')
        }),
        ('Goals', {
            'fields': ('goals_achievement_comment', 'goals_for_next_period')
        }),
        ('Recommendations', {
            'fields': ('promotion_recommendation', 'salary_increase_recommendation', 'training_recommendations')
        }),
        ('Overall', {
            'fields': ('overall_rating', 'manager_comments')
        }),
        ('Metadata', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_employee_name(self, obj):
        return obj.review.employee.get_full_name()
    get_employee_name.short_description = 'Employee'


@admin.register(PeerFeedback)
class PeerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['review', 'get_employee_name', 'peer', 'overall_rating', 'is_anonymous', 'submitted_at']
    list_filter = ['submitted_at', 'review__cycle', 'is_anonymous']
    search_fields = ['review__employee__username', 'peer__username']
    readonly_fields = ['submitted_at', 'updated_at']
    fieldsets = (
        ('Review & Peer', {
            'fields': ('review', 'peer', 'is_anonymous')
        }),
        ('Feedback', {
            'fields': ('collaboration_feedback', 'strengths', 'areas_for_improvement')
        }),
        ('Peer Ratings', {
            'fields': ('teamwork', 'communication', 'reliability', 'helpfulness')
        }),
        ('Overall', {
            'fields': ('overall_rating', 'additional_comments')
        }),
        ('Metadata', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_employee_name(self, obj):
        return obj.review.employee.get_full_name()
    get_employee_name.short_description = 'Employee'
