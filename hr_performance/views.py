"""
Views for Performance Management - Day 18
Goals, OKRs, KPIs, and Progress Tracking
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import GoalCategory, Goal, KPI, ProgressUpdate, Milestone, GoalComment
from .serializers import (
    GoalCategorySerializer, GoalListSerializer, GoalDetailSerializer,
    GoalCreateUpdateSerializer, KPISerializer, ProgressUpdateSerializer,
    MilestoneSerializer, GoalCommentSerializer, GoalProgressSerializer,
    KPIUpdateSerializer, KPIDashboardSerializer
)
from authentication.permissions import IsEmployee, IsManager, IsHR, IsAdmin


class GoalCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for goal categories
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GoalCategorySerializer
    queryset = GoalCategory.objects.all()
    
    def create(self, request, *args, **kwargs):
        """Only Admin/HR can create categories"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin or HR can create goal categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Only Admin/HR can update categories"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin or HR can update goal categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Only Admin/HR can delete categories"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'Only Admin or HR can delete goal categories'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for goals and OKRs
    Supports CRUD operations, progress tracking, and filtering
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter goals based on user role and permissions"""
        user = self.request.user
        
        if user.role == 'admin' or user.role == 'hr':
            # Admin and HR can see all goals
            queryset = Goal.objects.all()
        elif user.role == 'manager':
            # Managers can see their own goals, their team's goals, and company/department goals
            queryset = Goal.objects.filter(
                Q(owner=user) |
                Q(assigned_to=user) |
                Q(created_by=user) |
                Q(goal_type__in=['company', 'department', 'team'])
            ).distinct()
        else:
            # Employees can see their own goals (owner/assigned/created) and company/department goals
            queryset = Goal.objects.filter(
                Q(owner=user) |
                Q(assigned_to=user) |
                Q(created_by=user) |
                Q(goal_type__in=['company', 'department'])
            ).distinct()
        
        # Filtering
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        goal_type = self.request.query_params.get('goal_type')
        if goal_type:
            queryset = queryset.filter(goal_type=goal_type)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        is_okr = self.request.query_params.get('is_okr')
        if is_okr:
            queryset = queryset.filter(is_okr=is_okr.lower() == 'true')
        
        return queryset.select_related('owner', 'category', 'created_by').prefetch_related('assigned_to')
    
    def get_serializer_class(self):
        """Use different serializers for list and detail views"""
        if self.action == 'list':
            return GoalListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return GoalCreateUpdateSerializer
        return GoalDetailSerializer
    
    def update(self, request, *args, **kwargs):
        """Check permission before updating goal"""
        goal = self.get_object()
        user = request.user
        partial = kwargs.pop('partial', False)
        
        # Check permissions
        has_permission = False
        
        # Admin/HR can update any goal
        if user.role in ['admin', 'hr']:
            has_permission = True
        # Managers can update their own goals and team goals
        elif user.role == 'manager':
            if goal.owner == user or goal.created_by == user or goal.goal_type in ['team', 'department']:
                has_permission = True
        # Employees can update their own individual goals (owner or creator)
        elif goal.goal_type == 'individual' and (goal.owner == user or goal.created_by == user):
            has_permission = True
        # Or if employee is assigned to the goal
        elif user in goal.assigned_to.all():
            has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to update this goal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Perform update
        serializer = self.get_serializer(goal, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return detailed response with id and all fields
        response_serializer = GoalDetailSerializer(serializer.instance)
        return Response(response_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Check permission before deleting goal"""
        goal = self.get_object()
        user = request.user
        
        # Admin/HR can delete any goal
        if user.role in ['admin', 'hr']:
            return super().destroy(request, *args, **kwargs)
        
        # Managers can delete goals they own or created
        if user.role == 'manager' and (goal.owner == user or goal.created_by == user):
            return super().destroy(request, *args, **kwargs)
        
        # Employees can delete individual goals they own or created
        if (goal.owner == user or goal.created_by == user) and goal.goal_type == 'individual':
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'error': 'You do not have permission to delete this goal'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def create(self, request, *args, **kwargs):
        """Create goal and return detailed response with id"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Use detail serializer for response to include id and all fields
        response_serializer = GoalDetailSerializer(serializer.instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        """Set created_by to current user and enforce role-based restrictions"""
        goal_type = serializer.validated_data.get('goal_type')
        user = self.request.user
        
        # Check permissions based on goal type
        if goal_type == 'company':
            if user.role not in ['admin', 'hr']:
                raise PermissionError('Only Admin or HR can create company-level goals')
        elif goal_type == 'department':
            if user.role not in ['admin', 'hr']:
                raise PermissionError('Only Admin or HR can create department-level goals')
        elif goal_type == 'team':
            if user.role not in ['admin', 'hr', 'manager']:
                raise PermissionError('Only Managers or higher can create team goals')
        # individual goals can be created by anyone
        
        # Save the goal with created_by
        goal = serializer.save(created_by=self.request.user)
        
        # For individual goals, auto-assign the owner to the goal if not already assigned
        if goal_type == 'individual' and goal.owner and goal.owner not in goal.assigned_to.all():
            goal.assigned_to.add(goal.owner)
    
    @action(detail=False, methods=['get'], url_path='my-goals')
    def my_goals(self, request):
        """Get goals owned by, assigned to, or created by current user"""
        goals = Goal.objects.filter(
            Q(owner=request.user) | Q(assigned_to=request.user) | Q(created_by=request.user)
        ).distinct().select_related('owner', 'category', 'created_by').prefetch_related('assigned_to')
        
        serializer = GoalListSerializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='team-goals')
    def team_goals(self, request):
        """Get team and department goals"""
        goals = Goal.objects.filter(
            goal_type__in=['team', 'department', 'company']
        ).select_related('owner', 'category')
        
        serializer = GoalListSerializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update-progress')
    def update_progress(self, request, pk=None):
        """Update goal progress"""
        goal = self.get_object()
        user = request.user
        
        # Check permission - simplified to match update() logic
        has_permission = False
        
        # Admin/HR can update any goal progress
        if user.role in ['admin', 'hr']:
            has_permission = True
        # Managers can update their own goals and team goals
        elif user.role == 'manager':
            if goal.owner == user or goal.created_by == user or goal.goal_type in ['team', 'department']:
                has_permission = True
        # Employees can update goals they own, created, or are assigned to
        else:  # employee role
            # Can update if owner of an individual goal
            if goal.owner == user and goal.goal_type == 'individual':
                has_permission = True
            # Can update if they created the goal
            elif goal.created_by == user:
                has_permission = True
            # Can update if assigned to the goal
            elif user in goal.assigned_to.all():
                has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to update this goal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GoalProgressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Create progress update
        progress_update = ProgressUpdate.objects.create(
            goal=goal,
            updated_by=request.user,
            **serializer.validated_data
        )
        
        # Return updated goal
        goal.refresh_from_db()
        return Response(GoalDetailSerializer(goal).data)
    
    @action(detail=True, methods=['post'], url_path='add-milestone')
    def add_milestone(self, request, pk=None):
        """Add milestone to goal"""
        goal = self.get_object()
        user = request.user
        
        # Check permission - owner, creator, or Manager+
        has_permission = False
        
        if user.role in ['manager', 'hr', 'admin']:
            has_permission = True
        elif goal.owner == user or goal.created_by == user:
            has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to add milestones to this goal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MilestoneSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        milestone = serializer.save(goal=goal)
        return Response(MilestoneSerializer(milestone).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='add-comment')
    def add_comment(self, request, pk=None):
        """Add comment to goal"""
        goal = self.get_object()
        
        comment_text = request.data.get('comment')
        if not comment_text:
            return Response(
                {'error': 'Comment text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        parent_comment_id = request.data.get('parent_comment')
        parent_comment = None
        if parent_comment_id:
            try:
                parent_comment = GoalComment.objects.get(id=parent_comment_id, goal=goal)
            except GoalComment.DoesNotExist:
                return Response(
                    {'error': 'Parent comment not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        comment = GoalComment.objects.create(
            goal=goal,
            user=request.user,
            comment=comment_text,
            parent_comment=parent_comment
        )
        
        return Response(GoalCommentSerializer(comment).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='comments')
    def comments(self, request, pk=None):
        """Get all comments for a goal"""
        goal = self.get_object()
        comments = goal.comments.filter(parent_comment__isnull=True)  # Only root comments
        serializer = GoalCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Mark goal as completed"""
        goal = self.get_object()
        user = request.user
        
        # Check permission - same logic as update_progress
        has_permission = False
        
        # Admin/HR can complete any goal
        if user.role in ['admin', 'hr']:
            has_permission = True
        # Managers can complete their own goals and team goals
        elif user.role == 'manager':
            if goal.owner == user or goal.created_by == user or goal.goal_type in ['team', 'department']:
                has_permission = True
        # Employees can complete goals they own, created, or are assigned to
        else:  # employee role
            if goal.owner == user and goal.goal_type == 'individual':
                has_permission = True
            elif goal.created_by == user:
                has_permission = True
            elif user in goal.assigned_to.all():
                has_permission = True
        
        if not has_permission:
            return Response(
                {'error': 'You do not have permission to complete this goal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        goal.status = 'completed'
        goal.progress_percentage = 100
        goal.completed_date = timezone.now().date()
        goal.save()
        
        # Create completion progress update
        ProgressUpdate.objects.create(
            goal=goal,
            updated_by=request.user,
            progress_percentage=100,
            title="Goal Completed",
            description=request.data.get('completion_notes', 'Goal marked as completed')
        )
        
        return Response(GoalDetailSerializer(goal).data)
    
    @action(detail=False, methods=['get'], url_path='overdue')
    def overdue(self, request):
        """Get overdue goals"""
        today = timezone.now().date()
        goals = self.get_queryset().filter(
            due_date__lt=today,
            status__in=['draft', 'active', 'on_track', 'at_risk']
        )
        
        serializer = GoalListSerializer(goals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Get goal dashboard statistics"""
        user = request.user
        
        # Get user's goals
        my_goals = Goal.objects.filter(
            Q(owner=user) | Q(assigned_to=user)
        ).distinct()
        
        # Statistics
        total_goals = my_goals.count()
        active_goals = my_goals.filter(status__in=['active', 'on_track', 'at_risk']).count()
        completed_goals = my_goals.filter(status='completed').count()
        overdue_goals = my_goals.filter(
            due_date__lt=timezone.now().date(),
            status__in=['draft', 'active', 'on_track', 'at_risk']
        ).count()
        
        # Average progress
        avg_progress = my_goals.aggregate(Avg('progress_percentage'))['progress_percentage__avg'] or 0
        
        # Goals by status
        status_breakdown = {
            'draft': my_goals.filter(status='draft').count(),
            'active': my_goals.filter(status='active').count(),
            'on_track': my_goals.filter(status='on_track').count(),
            'at_risk': my_goals.filter(status='at_risk').count(),
            'completed': completed_goals,
            'cancelled': my_goals.filter(status='cancelled').count(),
        }
        
        # Recent goals
        recent_goals = my_goals.order_by('-created_at')[:5]
        
        return Response({
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'overdue_goals': overdue_goals,
            'average_progress': round(avg_progress, 2),
            'status_breakdown': status_breakdown,
            'recent_goals': GoalListSerializer(recent_goals, many=True).data
        })


class KPIViewSet(viewsets.ModelViewSet):
    """
    ViewSet for KPIs (Key Performance Indicators)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = KPISerializer
    
    def get_queryset(self):
        """Filter KPIs based on user role"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            queryset = KPI.objects.all()
        elif user.role == 'manager':
            # Managers can see their own and their team's KPIs
            queryset = KPI.objects.filter(
                Q(owner=user) | Q(owner__reporting_manager=user)
            )
        else:
            # Employees can only see their own KPIs
            queryset = KPI.objects.filter(owner=user)
        
        # Filtering
        is_active = self.request.query_params.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        frequency = self.request.query_params.get('frequency')
        if frequency:
            queryset = queryset.filter(frequency=frequency)
        
        return queryset.select_related('owner', 'category', 'related_goal')
    
    def perform_create(self, serializer):
        """Set owner to current user if not specified and enforce permissions"""
        user = self.request.user
        owner = serializer.validated_data.get('owner')
        
        # If no owner specified, set to current user
        if not owner:
            serializer.save(owner=user, created_by=user)
            return
        
        # Check if user can create KPI for someone else
        if owner != user:
            # Only Admin/HR/Manager can create KPIs for others
            if user.role not in ['admin', 'hr', 'manager']:
                raise PermissionError('You can only create KPIs for yourself')
            
            # Managers can only create KPIs for their team members
            if user.role == 'manager':
                if not hasattr(owner, 'reporting_manager') or owner.reporting_manager != user:
                    raise PermissionError('Managers can only create KPIs for their team members')
        
        serializer.save(created_by=user)
    
    def update(self, request, *args, **kwargs):
        """Check permission before updating KPI"""
        kpi = self.get_object()
        user = request.user
        
        # Admin/HR can update any KPI
        if user.role in ['admin', 'hr']:
            return super().update(request, *args, **kwargs)
        
        # Managers can update their own KPIs, created KPIs, and team members' KPIs
        if user.role == 'manager':
            if kpi.owner == user or kpi.created_by == user or (hasattr(kpi.owner, 'reporting_manager') and kpi.owner.reporting_manager == user):
                return super().update(request, *args, **kwargs)
        
        # Employees can update their own KPIs or KPIs they created
        if kpi.owner == user or kpi.created_by == user:
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'error': 'You do not have permission to update this KPI'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def destroy(self, request, *args, **kwargs):
        """Check permission before deleting KPI"""
        kpi = self.get_object()
        user = request.user
        
        # Admin/HR can delete any KPI
        if user.role in ['admin', 'hr']:
            return super().destroy(request, *args, **kwargs)
        
        # Managers can delete their own KPIs, created KPIs, and team members' KPIs
        if user.role == 'manager':
            if kpi.owner == user or kpi.created_by == user or (hasattr(kpi.owner, 'reporting_manager') and kpi.owner.reporting_manager == user):
                return super().destroy(request, *args, **kwargs)
        
        # Employees can delete their own KPIs or KPIs they created
        if kpi.owner == user or kpi.created_by == user:
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'error': 'You do not have permission to delete this KPI'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=False, methods=['get'], url_path='my-kpis')
    def my_kpis(self, request):
        """Get KPIs for current user"""
        kpis = KPI.objects.filter(owner=request.user, is_active=True)
        serializer = KPISerializer(kpis, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update-value')
    def update_value(self, request, pk=None):
        """Update KPI current value"""
        kpi = self.get_object()
        
        # Check permission
        if kpi.owner != request.user and request.user.role not in ['manager', 'hr', 'admin']:
            return Response(
                {'error': 'You do not have permission to update this KPI'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = KPIUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        kpi.current_value = serializer.validated_data['current_value']
        kpi.save()
        
        return Response(KPISerializer(kpi).data)
    
    @action(detail=False, methods=['get'], url_path='kpi-dashboard')
    def kpi_dashboard(self, request):
        """Get KPI dashboard with analytics"""
        user = request.user
        
        # Get user's KPIs
        my_kpis = KPI.objects.filter(owner=user)
        
        # Statistics
        total_kpis = my_kpis.count()
        active_kpis = my_kpis.filter(is_active=True).count()
        
        # Performance levels
        kpi_data = []
        on_track = 0
        at_risk = 0
        excellent = 0
        good = 0
        average = 0
        poor = 0
        
        for kpi in my_kpis.filter(is_active=True):
            kpi_data.append(KPISerializer(kpi).data)
            
            if kpi.is_on_track:
                on_track += 1
            else:
                at_risk += 1
            
            level = kpi.performance_level
            if level == 'excellent':
                excellent += 1
            elif level == 'good':
                good += 1
            elif level == 'average':
                average += 1
            else:
                poor += 1
        
        return Response({
            'total_kpis': total_kpis,
            'active_kpis': active_kpis,
            'on_track': on_track,
            'at_risk': at_risk,
            'excellent_performance': excellent,
            'good_performance': good,
            'average_performance': average,
            'poor_performance': poor,
            'kpis': kpi_data
        })


class ProgressUpdateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing progress updates
    Creating progress updates is done through Goal.update_progress action
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ProgressUpdateSerializer
    
    def get_queryset(self):
        """Filter progress updates based on user's accessible goals"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            return ProgressUpdate.objects.all()
        
        # Get goals user has access to
        accessible_goals = Goal.objects.filter(
            Q(owner=user) | Q(assigned_to=user)
        ).distinct()
        
        return ProgressUpdate.objects.filter(
            goal__in=accessible_goals
        ).select_related('goal', 'updated_by')


class MilestoneViewSet(viewsets.ModelViewSet):
    """
    ViewSet for milestones
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MilestoneSerializer
    
    def create(self, request, *args, **kwargs):
        """Only Managers and above can create milestones"""
        if request.user.role not in ['manager', 'hr', 'admin']:
            return Response(
                {'error': 'Only Managers, HR, or Admin can create milestones'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Only Managers and above can update milestones"""
        milestone = self.get_object()
        user = request.user
        
        if user.role in ['admin', 'hr']:
            return super().update(request, *args, **kwargs)
        
        if user.role == 'manager' and (milestone.goal.owner == user or milestone.goal.created_by == user or milestone.created_by == user):
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'error': 'You do not have permission to update this milestone'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def destroy(self, request, *args, **kwargs):
        """Only Managers and above can delete milestones"""
        milestone = self.get_object()
        user = request.user
        
        if user.role in ['admin', 'hr']:
            return super().destroy(request, *args, **kwargs)
        
        if user.role == 'manager' and (milestone.goal.owner == user or milestone.goal.created_by == user or milestone.created_by == user):
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'error': 'You do not have permission to delete this milestone'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def get_queryset(self):
        """Filter milestones based on user's accessible goals"""
        user = self.request.user
        
        if user.role in ['admin', 'hr']:
            return Milestone.objects.all()
        
        # Get goals user has access to - matching Goal.get_queryset() logic
        if user.role == 'manager':
            # Managers can see milestones for: own goals + team/department/company goals
            accessible_goals = Goal.objects.filter(
                Q(owner=user) | 
                Q(assigned_to=user) | 
                Q(created_by=user) |
                Q(goal_type__in=['company', 'department', 'team'])
            ).distinct()
        else:
            # Employees can see milestones for: own goals + company/department goals
            accessible_goals = Goal.objects.filter(
                Q(owner=user) | 
                Q(assigned_to=user) | 
                Q(created_by=user) |
                Q(goal_type__in=['company', 'department'])
            ).distinct()
        
        return Milestone.objects.filter(goal__in=accessible_goals).select_related('goal')
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Mark milestone as completed"""
        milestone = self.get_object()
        user = request.user
        goal = milestone.goal
        
        # Check permission: Admin/HR can complete any milestone
        if user.role in ['admin', 'hr']:
            milestone.status = 'completed'
            milestone.completed_date = timezone.now().date()
            milestone.save()
            return Response(MilestoneSerializer(milestone).data)
        
        # Manager can complete if they own/created the goal
        if user.role == 'manager' and (goal.owner == user or goal.created_by == user):
            milestone.status = 'completed'
            milestone.completed_date = timezone.now().date()
            milestone.save()
            return Response(MilestoneSerializer(milestone).data)
        
        # Employee can complete if owner or assigned to the goal
        if goal.owner == user or user in goal.assigned_to.all() or goal.created_by == user:
            milestone.status = 'completed'
            milestone.completed_date = timezone.now().date()
            milestone.save()
            return Response(MilestoneSerializer(milestone).data)
        
        return Response(
            {'error': 'You do not have permission to complete this milestone'},
            status=status.HTTP_403_FORBIDDEN
        )
