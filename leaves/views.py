from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q, Sum, Count
from datetime import date

from .models import Leave, LeaveType, LeaveBalance
from .serializers import (
    LeaveSerializer, LeaveTypeSerializer, 
    LeaveBalanceSerializer, LeaveApprovalSerializer,
    LeaveCalendarSerializer, TeamLeaveSerializer
)
from authentication.permissions import IsManager, IsManagerOrAbove


class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing leave types
    """
    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]


class LeaveBalanceView(APIView):
    """
    Get leave balance for the authenticated user
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_year = date.today().year
        year = request.query_params.get('year', current_year)
        
        balances = LeaveBalance.objects.filter(
            user=request.user,
            year=year
        ).select_related('leave_type')
        
        serializer = LeaveBalanceSerializer(balances, many=True)
        return Response(serializer.data)


class LeaveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for leave management
    """
    serializer_class = LeaveSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Admin and HR can see all leaves
        if user.role in ['admin', 'hr']:
            return Leave.objects.all().select_related('user', 'leave_type', 'approved_by', 'applied_to', 'secondary_approver')
        
        # Managers can see their team's leaves
        if user.role == 'manager':
            return Leave.objects.filter(
                Q(user=user) | Q(applied_to=user)
            ).select_related('user', 'leave_type', 'approved_by')
        
        # Employees see only their leaves
        return Leave.objects.filter(user=user).select_related(
            'leave_type', 'approved_by'
        )

    def get_permissions(self):
        if self.action in ['approve_reject']:
            return [IsAuthenticated(), IsManagerOrAbove()]
        return super().get_permissions()

    @action(detail=False, methods=['post'], url_path='apply')
    def apply_leave(self, request):
        """
        Apply for leave
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        leave = serializer.save()
        
        # Update leave balance
        self.update_leave_balance(leave)
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='history')
    def leave_history(self, request):
        """
        Get leave history for the user
        """
        leaves = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            leaves = leaves.filter(status=status_filter)
        
        year = request.query_params.get('year')
        if year:
            leaves = leaves.filter(start_date__year=year)
        
        page = self.paginate_queryset(leaves)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(leaves, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pending-approvals')
    def pending_approvals(self, request):
        """
        Get pending leave approvals (for managers, HR, and admins)
        """
        if request.user.role not in ['manager', 'hr', 'admin']:
            return Response(
                {'error': 'Only managers, HR, and admins can view pending approvals'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Managers see leaves where they are the approver
        # HR/Admin see leaves where they are primary or secondary approver
        if request.user.role == 'manager':
            pending_leaves = Leave.objects.filter(
                applied_to=request.user,
                status='pending'
            ).select_related('user', 'leave_type')
        else:
            # HR and Admin can see all pending leaves or those assigned to them
            pending_leaves = Leave.objects.filter(
                Q(applied_to=request.user) | Q(secondary_approver=request.user),
                status='pending'
            ).select_related('user', 'leave_type')
        
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve-reject')
    def approve_reject(self, request, pk=None):
        """
        Approve or reject a leave request (supports multi-level approval)
        """
        leave = self.get_object()
        
        # Check if user can approve this leave
        if not leave.can_be_approved_by(request.user):
            return Response(
                {'error': 'You are not authorized to approve/reject this leave at this level'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if leave.status != 'pending':
            return Response(
                {'error': f'Leave is already {leave.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval_serializer = LeaveApprovalSerializer(data=request.data)
        approval_serializer.is_valid(raise_exception=True)
        
        action_type = approval_serializer.validated_data['action']
        
        if action_type == 'approve':
            # Check if multi-level approval is required
            if leave.requires_multi_level:
                # Advance to next level
                needs_more_approval = leave.advance_approval_level()
                
                if needs_more_approval:
                    leave.save()
                    message = f'Leave approved at level {leave.current_approval_level - 1}. Forwarded to next approver.'
                else:
                    # Final approval
                    leave.status = 'approved'
                    leave.approved_by = request.user
                    leave.approved_at = timezone.now()
                    leave.save()
                    
                    # Update leave balance - deduct used days
                    self.update_leave_balance(leave, approve=True)
                    
                    message = 'Leave fully approved successfully'
            else:
                # Single level approval
                leave.status = 'approved'
                leave.approved_by = request.user
                leave.approved_at = timezone.now()
                leave.save()
                
                # Update leave balance - deduct used days
                self.update_leave_balance(leave, approve=True)
                
                message = 'Leave approved successfully'
        else:
            # Reject at any level
            leave.status = 'rejected'
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.rejection_reason = approval_serializer.validated_data.get('rejection_reason', '')
            leave.save()
            
            message = 'Leave rejected successfully'
        
        serializer = self.get_serializer(leave)
        return Response({
            'message': message,
            'leave': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_leave(self, request, pk=None):
        """
        Cancel a leave request
        """
        leave = self.get_object()
        
        # Only the user who applied can cancel
        if leave.user != request.user:
            return Response(
                {'error': 'You can only cancel your own leaves'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if leave.status not in ['pending', 'approved']:
            return Response(
                {'error': 'Only pending or approved leaves can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If leave was approved, restore the balance
        if leave.status == 'approved':
            self.restore_leave_balance(leave)
        
        leave.status = 'cancelled'
        leave.save()
        
        serializer = self.get_serializer(leave)
        return Response({
            'message': 'Leave cancelled successfully',
            'leave': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='calendar')
    def leave_calendar(self, request):
        """
        Get leave calendar view for a specific month/year
        Shows all approved and pending leaves
        """
        # Get query parameters
        month = request.query_params.get('month', date.today().month)
        year = request.query_params.get('year', date.today().year)
        
        try:
            month = int(month)
            year = int(year)
        except ValueError:
            return Response(
                {'error': 'Invalid month or year format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get leaves for the specified month
        leaves = Leave.objects.filter(
            start_date__year=year,
            start_date__month=month,
            status__in=['pending', 'approved']
        ).select_related('user', 'leave_type')
        
        # Managers can see team leaves, employees see all
        if request.user.role == 'employee':
            leaves = leaves.filter(user=request.user)
        
        serializer = LeaveCalendarSerializer(leaves, many=True)
        return Response({
            'month': month,
            'year': year,
            'leaves': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='team-leaves')
    def team_leaves(self, request):
        """
        Get team leave view (for managers)
        Shows all leaves of team members
        """
        if request.user.role not in ['manager', 'admin', 'hr']:
            return Response(
                {'error': 'Only managers, HR, and admins can view team leaves'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get team leaves
        if request.user.role == 'manager':
            team_leaves = Leave.objects.filter(
                applied_to=request.user
            ).select_related('user', 'leave_type')
        else:
            # HR and Admin can see all leaves
            team_leaves = Leave.objects.all().select_related('user', 'leave_type')
        
        # Apply filters
        status_filter = request.query_params.get('status')
        if status_filter:
            team_leaves = team_leaves.filter(status=status_filter)
        
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        if month and year:
            try:
                team_leaves = team_leaves.filter(
                    start_date__month=int(month),
                    start_date__year=int(year)
                )
            except ValueError:
                pass
        
        serializer = TeamLeaveSerializer(team_leaves, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='approval-stats')
    def approval_stats(self, request):
        """
        Get approval statistics (for managers)
        """
        if request.user.role not in ['manager', 'admin', 'hr']:
            return Response(
                {'error': 'Only managers, HR, and admins can view approval statistics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get pending approvals count
        pending_count = Leave.objects.filter(
            Q(applied_to=request.user) | Q(secondary_approver=request.user),
            status='pending'
        ).count()
        
        # Get approval history for current month
        current_month_approvals = Leave.objects.filter(
            approved_by=request.user,
            approved_at__month=date.today().month,
            approved_at__year=date.today().year
        ).aggregate(
            total_approved=Count('id', filter=Q(status='approved')),
            total_rejected=Count('id', filter=Q(status='rejected'))
        )
        
        return Response({
            'pending_approvals': pending_count,
            'this_month': {
                'approved': current_month_approvals['total_approved'] or 0,
                'rejected': current_month_approvals['total_rejected'] or 0
            }
        })

    def update_leave_balance(self, leave, approve=False):
        """
        Update leave balance when leave is applied or approved
        """
        current_year = date.today().year
        
        balance, created = LeaveBalance.objects.get_or_create(
            user=leave.user,
            leave_type=leave.leave_type,
            year=current_year,
            defaults={
                'total_days': leave.leave_type.default_days,
                'used_days': 0,
                'available_days': leave.leave_type.default_days
            }
        )
        
        if approve:
            # Deduct from balance when approved
            balance.used_days += leave.total_days
            balance.update_balance()

    def restore_leave_balance(self, leave):
        """
        Restore leave balance when leave is cancelled
        """
        current_year = date.today().year
        
        try:
            balance = LeaveBalance.objects.get(
                user=leave.user,
                leave_type=leave.leave_type,
                year=current_year
            )
            balance.used_days -= leave.total_days
            balance.update_balance()
        except LeaveBalance.DoesNotExist:
            pass
