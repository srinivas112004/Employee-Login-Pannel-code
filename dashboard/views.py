"""
Dashboard App - Views
Day 4: API views for employee dashboard.
Day 6: Added Project, Milestone, Subtask, and File Attachment views.
"""

from rest_framework import status, generics, parsers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime
import os

from .models import Announcement, Task, LeaveBalance, Project, Milestone, FileAttachment
from .serializers import (
    AnnouncementSerializer,
    TaskSerializer,
    LeaveBalanceSerializer,
    DashboardSummarySerializer,
    TaskSummarySerializer,
    ProjectSerializer,
    ProjectDetailSerializer,
    MilestoneSerializer,
    SubtaskSerializer,
    FileAttachmentSerializer
)
from authentication.models import User


# ==============================================================================
# DAY 4: Dashboard Summary API
# ==============================================================================

class DashboardSummaryView(APIView):
    """
    API endpoint for dashboard summary.
    Returns overview of key metrics for the user.
    
    GET /api/dashboard/summary/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary data."""
        user = request.user
        current_year = timezone.now().year
        
        # Get total employees (for admin/manager)
        if user.role in ['admin', 'manager']:
            total_employees = User.objects.filter(is_active=True).count()
        else:
            total_employees = None
        
        # Get task statistics
        if user.role in ['admin', 'manager']:
            all_tasks = Task.objects.all()
        else:
            all_tasks = Task.objects.filter(assigned_to=user)
        
        active_tasks = all_tasks.filter(status__in=['todo', 'in_progress']).count()
        completed_tasks = all_tasks.filter(status='completed').count()
        pending_tasks = all_tasks.filter(status='todo').count()
        overdue_tasks = all_tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        
        # Get recent announcements
        recent_announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5]
        
        # Get user's tasks summary
        my_tasks = Task.objects.filter(assigned_to=user)
        my_tasks_summary = {
            'total': my_tasks.count(),
            'pending': my_tasks.filter(status='todo').count(),
            'in_progress': my_tasks.filter(status='in_progress').count(),
            'completed': my_tasks.filter(status='completed').count(),
        }
        
        # Get leave summary for current user
        leave_balances = LeaveBalance.objects.filter(user=user, year=current_year)
        leave_summary = {}
        for leave in leave_balances:
            leave_summary[leave.leave_type] = {
                'total': float(leave.total_days),
                'used': float(leave.used_days),
                'remaining': leave.remaining_days
            }
        
        # Prepare response data
        summary_data = {
            'total_employees': total_employees,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'recent_announcements': AnnouncementSerializer(recent_announcements, many=True).data,
            'my_tasks_summary': my_tasks_summary,
            'leave_summary': leave_summary,
        }
        
        return Response(summary_data, status=status.HTTP_200_OK)


# ==============================================================================
# DAY 4: Task Summary API
# ==============================================================================

class TaskSummaryView(APIView):
    """
    API endpoint for task statistics.
    Returns detailed task statistics by status and priority.
    
    GET /api/dashboard/tasks-summary/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get task summary statistics."""
        user = request.user
        
        # Get tasks based on user role
        if user.role in ['admin', 'manager']:
            tasks = Task.objects.all()
        else:
            tasks = Task.objects.filter(assigned_to=user)
        
        # Count by status
        total_tasks = tasks.count()
        todo = tasks.filter(status='todo').count()
        in_progress = tasks.filter(status='in_progress').count()
        review = tasks.filter(status='review').count()
        completed = tasks.filter(status='completed').count()
        cancelled = tasks.filter(status='cancelled').count()
        
        # Count overdue tasks
        overdue = tasks.filter(
            status__in=['todo', 'in_progress'],
            due_date__lt=timezone.now()
        ).count()
        
        # Count by priority
        by_priority = {
            'low': tasks.filter(priority='low').count(),
            'medium': tasks.filter(priority='medium').count(),
            'high': tasks.filter(priority='high').count(),
            'urgent': tasks.filter(priority='urgent').count(),
        }
        
        # Get recent tasks
        recent_tasks = tasks.order_by('-created_at')[:10]
        
        summary_data = {
            'total_tasks': total_tasks,
            'todo': todo,
            'in_progress': in_progress,
            'review': review,
            'completed': completed,
            'cancelled': cancelled,
            'overdue': overdue,
            'by_priority': by_priority,
            'recent_tasks': TaskSerializer(recent_tasks, many=True).data,
        }
        
        return Response(summary_data, status=status.HTTP_200_OK)


# ==============================================================================
# DAY 4: Leave Balance API
# ==============================================================================

class LeaveBalanceView(APIView):
    """
    API endpoint for leave balance.
    Returns user's leave balances for current year.
    
    GET /api/dashboard/leave-balance/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user's leave balance."""
        user = request.user
        current_year = timezone.now().year
        
        # Get all leave balances for current year
        leave_balances = LeaveBalance.objects.filter(user=user, year=current_year)
        
        if not leave_balances.exists():
            return Response({
                'message': 'No leave balances found for current year',
                'leave_balances': []
            }, status=status.HTTP_200_OK)
        
        serializer = LeaveBalanceSerializer(leave_balances, many=True)
        
        # Calculate totals
        total_allocated = sum(float(lb.total_days) for lb in leave_balances)
        total_used = sum(float(lb.used_days) for lb in leave_balances)
        total_remaining = total_allocated - total_used
        
        return Response({
            'year': current_year,
            'leave_balances': serializer.data,
            'summary': {
                'total_allocated': total_allocated,
                'total_used': total_used,
                'total_remaining': total_remaining,
                'usage_percentage': (total_used / total_allocated * 100) if total_allocated > 0 else 0
            }
        }, status=status.HTTP_200_OK)


# ==============================================================================
# DAY 4: Announcements CRUD APIs
# ==============================================================================

class AnnouncementListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create announcements.
    
    GET /api/dashboard/announcements/ - List all active announcements
    POST /api/dashboard/announcements/ - Create new announcement (Admin/Manager only)
    """
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get active announcements, optionally filtered by priority."""
        queryset = Announcement.objects.filter(is_active=True)
        
        # Filter by priority if provided
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create announcement (only admin/manager can create)."""
        if self.request.user.role not in ['admin', 'manager']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins and managers can create announcements")
        
        serializer.save(created_by=self.request.user)


class AnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete an announcement.
    
    GET /api/dashboard/announcements/{id}/ - Get announcement details
    PUT /api/dashboard/announcements/{id}/ - Update announcement (Admin/Manager only)
    DELETE /api/dashboard/announcements/{id}/ - Delete announcement (Admin/Manager only)
    """
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_update(self, serializer):
        """Update announcement (only admin/manager can update)."""
        if self.request.user.role not in ['admin', 'manager']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins and managers can update announcements")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Delete announcement (only admin/manager can delete)."""
        if self.request.user.role not in ['admin', 'manager']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins and managers can delete announcements")
        
        instance.delete()


# ==============================================================================
# DAY 4: Task APIs (Basic CRUD)
# ==============================================================================

class TaskListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list and create tasks.
    
    GET /api/dashboard/tasks/ - List tasks
    POST /api/dashboard/tasks/ - Create new task (Admin/Manager only)
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get tasks based on user role and filters."""
        user = self.request.user
        
        # Admin/Manager can see all tasks, employees see their own
        if user.role in ['admin', 'manager']:
            queryset = Task.objects.all()
        else:
            queryset = Task.objects.filter(assigned_to=user)
        
        # Filter by status
        task_status = self.request.query_params.get('status', None)
        if task_status:
            queryset = queryset.filter(status=task_status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Create task (only admin/manager can create)."""
        if self.request.user.role not in ['admin', 'manager']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins and managers can create tasks")
        
        # Save the task
        task = serializer.save(assigned_by=self.request.user)
        
        # Trigger assignment notification (Day 7)
        try:
            from notifications.tasks import send_task_assignment_notification
            send_task_assignment_notification.delay(task.id)
        except ImportError:
            # notifications app not installed yet
            pass


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a task.
    
    GET /api/dashboard/tasks/{id}/ - Get task details
    PUT /api/dashboard/tasks/{id}/ - Update task
    DELETE /api/dashboard/tasks/{id}/ - Delete task (Admin/Manager only)
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tasks based on user role."""
        user = self.request.user
        if user.role in ['admin', 'manager']:
            return Task.objects.all()
        return Task.objects.filter(assigned_to=user)
    
    def perform_destroy(self, instance):
        """Delete task (only admin/manager can delete)."""
        if self.request.user.role not in ['admin', 'manager']:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins and managers can delete tasks")
        
        instance.delete()


# ============================================================
# DAY 6: PROJECT MANAGEMENT VIEWS
# ============================================================

class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET: List all projects (employees see assigned projects, managers see all)
    POST: Create new project (managers and admins only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        """Filter projects based on user role."""
        user = self.request.user
        if user.role in ['admin', 'manager']:
            # Admins and managers see all projects
            return Project.objects.all()
        else:
            # Employees/interns see only projects they're assigned to
            return Project.objects.filter(assigned_to=user).distinct()
    
    def perform_create(self, serializer):
        """Create project - only managers and admins."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can create projects")
        
        try:
            # Handle both 'members' and 'assigned_to' fields from frontend
            assigned_to = self.request.data.get('assigned_to', self.request.data.get('members', []))
            
            # Save the project
            project = serializer.save(created_by=self.request.user)
            
            # Set assigned_to if provided
            if assigned_to:
                project.assigned_to.set(assigned_to)
            
            return project
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating project: {str(e)}")
            logger.error(f"Request data: {self.request.data}")
            raise ValidationError(f"Failed to create project: {str(e)}")


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get project details with tasks, milestones, and attachments
    PUT/PATCH: Update project (managers and admins only)
    DELETE: Delete project (admins only)
    """
    permission_classes = [IsAuthenticated]
    queryset = Project.objects.all()
    
    def get_serializer_class(self):
        """Use detailed serializer for GET, basic for PUT/PATCH."""
        if self.request.method == 'GET':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def perform_update(self, serializer):
        """Update project - only managers and admins."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can update projects")
        
        # Handle 'members' field from frontend (should be mapped to 'assigned_to')
        members = self.request.data.get('members', None)
        project = serializer.save()
        
        # Update assigned_to (members) if provided
        if members is not None:
            project.assigned_to.set(members)
        
        return project
    
    def perform_destroy(self, instance):
        """Delete project - admins and managers."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can delete projects")
        
        instance.delete()


class MilestoneListCreateView(generics.ListCreateAPIView):
    """
    GET: List milestones for a project
    POST: Create milestone (managers and admins only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer
    
    def get_queryset(self):
        """Get milestones for the specified project."""
        project_id = self.kwargs.get('project_id')
        return Milestone.objects.filter(project_id=project_id)
    
    def perform_create(self, serializer):
        """Create milestone - only managers and admins."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can create milestones")
        
        project_id = self.kwargs.get('project_id')
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            raise ValidationError("Project not found")
        
        serializer.save(project=project)


class MilestoneDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get milestone details
    PUT/PATCH: Update milestone (managers and admins only)
    DELETE: Delete milestone (admins only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer
    queryset = Milestone.objects.all()
    
    def perform_update(self, serializer):
        """Update milestone - only managers and admins."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can update milestones")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Delete milestone - admins and managers."""
        if self.request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can delete milestones")
        
        instance.delete()


class SubtaskListCreateView(generics.ListCreateAPIView):
    """
    GET: List subtasks for a parent task
    POST: Create subtask under parent task
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubtaskSerializer
    
    def get_queryset(self):
        """Get subtasks for the specified parent task."""
        parent_task_id = self.kwargs.get('task_id')
        return Task.objects.filter(parent_task_id=parent_task_id)
    
    def perform_create(self, serializer):
        """Create subtask."""
        parent_task_id = self.kwargs.get('task_id')
        try:
            parent_task = Task.objects.get(id=parent_task_id)
        except Task.DoesNotExist:
            raise ValidationError("Parent task not found")
        
        # Inherit project from parent task
        serializer.save(
            parent_task=parent_task,
            project=parent_task.project,
            assigned_by=self.request.user
        )


class FileAttachmentUploadView(generics.ListCreateAPIView):
    """
    GET: List attachments for task or project
    POST: Upload file attachment
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FileAttachmentSerializer
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def get_queryset(self):
        """Get attachments based on query parameters."""
        task_id = self.request.query_params.get('task_id')
        project_id = self.request.query_params.get('project_id')
        
        queryset = FileAttachment.objects.all()
        
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        elif project_id:
            queryset = queryset.filter(project_id=project_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Upload file with validation."""
        file = self.request.FILES.get('file')
        
        if not file:
            raise ValidationError("No file provided")
        
        # File size validation (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if file.size > max_size:
            raise ValidationError(f"File size exceeds 10MB limit. Current size: {file.size / (1024*1024):.2f}MB")
        
        # File type validation (allow common formats)
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.png', '.jpg', '.jpeg', '.gif', '.zip']
        file_ext = os.path.splitext(file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise ValidationError(f"File type {file_ext} not allowed. Allowed types: {', '.join(allowed_extensions)}")
        
        serializer.save(
            uploaded_by=self.request.user,
            file_name=file.name,
            file_type=file_ext,
            file_size=file.size
        )


class FileAttachmentDeleteView(generics.DestroyAPIView):
    """
    DELETE: Delete file attachment (uploader, admins, or managers only)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FileAttachmentSerializer
    queryset = FileAttachment.objects.all()
    
    def perform_destroy(self, instance):
        """Delete file - uploader, admin, or manager only."""
        user = self.request.user
        
        if user != instance.uploaded_by and user.role not in ['admin', 'manager']:
            raise PermissionDenied("You can only delete your own attachments, or be an admin/manager")
        
        # Delete the physical file
        if instance.file:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
        
        instance.delete()
