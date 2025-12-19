"""
Dashboard App - URL Configuration
Maps URLs to dashboard views.
Day 6: Added project management URLs.
"""

from django.urls import path
from .views import (
    DashboardSummaryView,
    TaskSummaryView,
    LeaveBalanceView,
    AnnouncementListCreateView,
    AnnouncementDetailView,
    TaskListCreateView,
    TaskDetailView,
    # Day 6: Project Management
    ProjectListCreateView,
    ProjectDetailView,
    MilestoneListCreateView,
    MilestoneDetailView,
    SubtaskListCreateView,
    FileAttachmentUploadView,
    FileAttachmentDeleteView,
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Summary
    path('summary/', DashboardSummaryView.as_view(), name='dashboard_summary'),
    
    # Task Summary
    path('tasks-summary/', TaskSummaryView.as_view(), name='tasks_summary'),
    
    # Leave Balance
    path('leave-balance/', LeaveBalanceView.as_view(), name='leave_balance'),
    
    # Announcements
    path('announcements/', AnnouncementListCreateView.as_view(), name='announcement_list'),
    path('announcements/<int:pk>/', AnnouncementDetailView.as_view(), name='announcement_detail'),
    
    # Tasks
    path('tasks/', TaskListCreateView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task_detail'),
    
    # ============================================================
    # DAY 6: PROJECT MANAGEMENT URLS
    # ============================================================
    
    # Projects
    path('projects/', ProjectListCreateView.as_view(), name='project_list'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    
    # Milestones
    path('projects/<int:project_id>/milestones/', MilestoneListCreateView.as_view(), name='milestone_list'),
    path('milestones/<int:pk>/', MilestoneDetailView.as_view(), name='milestone_detail'),
    
    # Subtasks
    path('tasks/<int:task_id>/subtasks/', SubtaskListCreateView.as_view(), name='subtask_list'),
    
    # File Attachments
    path('attachments/', FileAttachmentUploadView.as_view(), name='attachment_upload'),
    path('attachments/<int:pk>/', FileAttachmentDeleteView.as_view(), name='attachment_delete'),
]
