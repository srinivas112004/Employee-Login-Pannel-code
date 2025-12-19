from django.contrib import admin
from .models import GoalCategory, Goal, KPI, ProgressUpdate, Milestone, GoalComment


@admin.register(GoalCategory)
class GoalCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'created_at']
    search_fields = ['name']


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'goal_type', 'status', 'priority', 'progress_percentage', 'due_date', 'is_overdue']
    list_filter = ['status', 'priority', 'goal_type', 'is_okr']
    search_fields = ['title', 'description', 'owner__email']
    filter_horizontal = ['assigned_to']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'goal_type', 'priority', 'is_okr', 'parent_goal')
        }),
        ('Assignment', {
            'fields': ('owner', 'assigned_to', 'created_by')
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date', 'completed_date')
        }),
        ('Progress', {
            'fields': ('status', 'progress_percentage', 'target_value', 'current_value', 'unit')
        }),
    )


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'current_value', 'target_value', 'achievement_percentage', 'performance_level', 'frequency']
    list_filter = ['frequency', 'is_active', 'category']
    search_fields = ['name', 'description', 'owner__email']
    date_hierarchy = 'created_at'


@admin.register(ProgressUpdate)
class ProgressUpdateAdmin(admin.ModelAdmin):
    list_display = ['goal', 'updated_by', 'progress_percentage', 'help_needed', 'created_at']
    list_filter = ['help_needed', 'created_at']
    search_fields = ['title', 'description', 'goal__title']
    date_hierarchy = 'created_at'


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal', 'status', 'due_date', 'is_overdue']
    list_filter = ['status']
    search_fields = ['title', 'goal__title']
    date_hierarchy = 'due_date'


@admin.register(GoalComment)
class GoalCommentAdmin(admin.ModelAdmin):
    list_display = ['goal', 'user', 'comment', 'created_at']
    search_fields = ['comment', 'goal__title', 'user__email']
    date_hierarchy = 'created_at'
