from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import EmployeeProfile, EmployeeDocument, OnboardingChecklist, EmploymentHistory
from .serializers import (
    EmployeeProfileSerializer, 
    EmployeeProfileListSerializer,
    EmployeeDocumentSerializer,
    OnboardingChecklistSerializer,
    EmploymentHistorySerializer
)


class EmployeeProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for employee profile management
    - Admin/HR: Full access to all profiles
    - Manager: Can view team members' profiles
    - Employee: Can view own profile only
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeProfileListSerializer
        return EmployeeProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and HR can see all profiles
        if user.role in ['admin', 'hr']:
            return EmployeeProfile.objects.all().select_related(
                'user', 'reporting_manager'
            ).prefetch_related(
                'documents', 'onboarding_tasks', 'employment_history'
            )
        
        # Managers can see their team members
        elif user.role == 'manager':
            return EmployeeProfile.objects.filter(
                reporting_manager=user
            ).select_related('user', 'reporting_manager')
        
        # Employees can see only their own profile
        else:
            return EmployeeProfile.objects.filter(user=user).select_related(
                'user', 'reporting_manager'
            ).prefetch_related(
                'documents', 'onboarding_tasks', 'employment_history'
            )
    
    def create(self, request, *args, **kwargs):
        """Create employee profile - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create employee profiles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update employee profile"""
        profile = self.get_object()
        
        # Admin/HR can update any profile
        if request.user.role in ['admin', 'hr']:
            # Support partial updates
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        # Employees can update their own profile
        if profile.user == request.user:
            # Support partial updates
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to update this profile.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) employee profile"""
        profile = self.get_object()
        
        # Admin/HR can update any profile
        if request.user.role in ['admin', 'hr']:
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        # Employees can update their own profile
        if profile.user == request.user:
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to update this profile.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete employee profile - Admin only"""
        if request.user.role != 'admin':
            return Response(
                {'detail': 'Only Admin can delete employee profiles.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get current user's profile"""
        try:
            profile = EmployeeProfile.objects.select_related(
                'user', 'reporting_manager'
            ).prefetch_related(
                'documents', 'onboarding_tasks', 'employment_history'
            ).get(user=request.user)
            
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'detail': 'You do not have an employee profile yet.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def complete_onboarding(self, request, pk=None):
        """Mark onboarding as complete - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can complete onboarding.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        profile = self.get_object()
        
        # Check if all tasks are completed
        pending_tasks = profile.onboarding_tasks.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        )
        
        if pending_tasks.exists():
            return Response(
                {
                    'detail': 'Cannot complete onboarding. Some tasks are still pending.',
                    'pending_tasks': [task.task_name for task in pending_tasks]
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark onboarding as complete
        profile.onboarding_completed = True
        profile.onboarding_completed_date = timezone.now()
        profile.save()
        
        serializer = self.get_serializer(profile)
        return Response({
            'message': 'Onboarding completed successfully',
            'profile': serializer.data
        })


class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for employee document management
    """
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and HR can see all documents
        if user.role in ['admin', 'hr']:
            queryset = EmployeeDocument.objects.all()
        else:
            # Employees can see only their own documents
            queryset = EmployeeDocument.objects.filter(employee__user=user)
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.select_related('employee', 'verified_by')
    
    def create(self, request, *args, **kwargs):
        """Upload document"""
        # Get employee from request or default to current user's profile
        employee_id = request.data.get('employee')
        
        if not employee_id:
            # Try to get current user's profile
            try:
                profile = EmployeeProfile.objects.get(user=request.user)
                request.data['employee'] = profile.id
            except EmployeeProfile.DoesNotExist:
                return Response(
                    {'detail': 'You do not have an employee profile.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Verify employee exists
            if not EmployeeProfile.objects.filter(id=employee_id).exists():
                return Response(
                    {'detail': 'Employee profile not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete document - Admin/HR or owner"""
        document = self.get_object()
        
        # Admin/HR can delete any document
        if request.user.role in ['admin', 'hr']:
            return super().destroy(request, *args, **kwargs)
        
        # Employees can delete their own documents
        if document.employee.user == request.user:
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to delete this document.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify document - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can verify documents.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document = self.get_object()
        
        if document.is_verified:
            return Response(
                {'detail': 'Document is already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as verified
        document.is_verified = True
        document.verified_by = request.user
        document.verified_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response({
            'message': 'Document verified successfully',
            'document': serializer.data
        })


class OnboardingChecklistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for onboarding checklist management
    """
    serializer_class = OnboardingChecklistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and HR can see all tasks
        if user.role in ['admin', 'hr']:
            queryset = OnboardingChecklist.objects.all()
        else:
            # Employees can see only their own tasks
            queryset = OnboardingChecklist.objects.filter(employee__user=user)
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.select_related('employee', 'assigned_to', 'completed_by')
    
    def create(self, request, *args, **kwargs):
        """Create onboarding task - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create onboarding tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update onboarding task"""
        task = self.get_object()
        
        # Admin/HR can update any task
        if request.user.role in ['admin', 'hr']:
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        # Employees can update their own tasks (limited fields)
        if task.employee.user == request.user:
            # Only allow status and notes updates
            allowed_fields = ['status', 'notes']
            for field in request.data:
                if field not in allowed_fields:
                    return Response(
                        {'detail': f'You can only update: {", ".join(allowed_fields)}'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to update this task.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) onboarding task"""
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete onboarding task - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can delete onboarding tasks.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark task as completed"""
        task = self.get_object()
        
        # Check permission
        if request.user.role not in ['admin', 'hr'] and task.employee.user != request.user:
            return Response(
                {'detail': 'You do not have permission to complete this task.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if task.status == 'COMPLETED':
            return Response(
                {'detail': 'Task is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as completed
        task.status = 'COMPLETED'
        task.completed_by = request.user
        task.completed_at = timezone.now()
        
        # Update notes if provided
        notes = request.data.get('notes')
        if notes:
            task.notes = notes
        
        task.save()
        
        serializer = self.get_serializer(task)
        return Response({
            'message': 'Task completed successfully',
            'task': serializer.data
        })


class EmploymentHistoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for employment history management
    """
    serializer_class = EmploymentHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin and HR can see all employment history
        if user.role in ['admin', 'hr']:
            queryset = EmploymentHistory.objects.all()
        else:
            # Employees can see only their own history
            queryset = EmploymentHistory.objects.filter(employee__user=user)
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.select_related('employee')
    
    def create(self, request, *args, **kwargs):
        """Add employment record"""
        # Verify employee exists
        employee_id = request.data.get('employee')
        if not employee_id:
            return Response(
                {'detail': 'Employee ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = EmployeeProfile.objects.get(id=employee_id)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'detail': 'Employee profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission
        if request.user.role not in ['admin', 'hr'] and employee.user != request.user:
            return Response(
                {'detail': 'You can only add your own employment history.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update employment record"""
        record = self.get_object()
        
        # Admin/HR can update any record
        if request.user.role in ['admin', 'hr']:
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        # Employees can update their own records
        if record.employee.user == request.user:
            kwargs['partial'] = True
            return super().update(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to update this record.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) employment record"""
        return self.update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete employment record"""
        record = self.get_object()
        
        # Admin/HR can delete any record
        if request.user.role in ['admin', 'hr']:
            return super().destroy(request, *args, **kwargs)
        
        # Employees can delete their own records
        if record.employee.user == request.user:
            return super().destroy(request, *args, **kwargs)
        
        return Response(
            {'detail': 'You do not have permission to delete this record.'},
            status=status.HTTP_403_FORBIDDEN
        )
