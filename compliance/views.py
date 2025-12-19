"""
Views for Compliance and Policy Management
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from .models import PolicyCategory, Policy, PolicyAcknowledgment, ComplianceReminder
from .serializers import (
    PolicyCategorySerializer, PolicyListSerializer, PolicyDetailSerializer,
    PolicyCreateUpdateSerializer, PolicyAcknowledgmentSerializer,
    AcknowledgeRequestSerializer, ComplianceStatusSerializer,
    UserComplianceReportSerializer
)
from authentication.permissions import IsAdminOrHR


def get_client_ip(request):
    """Get client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PolicyCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Policy Categories
    
    Permissions:
    - list, retrieve: All authenticated users
    - create, update, delete: Admin/HR only
    """
    queryset = PolicyCategory.objects.all()
    serializer_class = PolicyCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOrHR()]
        return [IsAuthenticated()]


class PolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Policies
    
    Permissions:
    - list, retrieve: All authenticated users
    - create, update, delete: Admin/HR only
    - acknowledge: All authenticated users (for assigned policies)
    - publish: Admin/HR only
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter policies based on user role and status"""
        user = self.request.user
        queryset = Policy.objects.select_related('category', 'created_by', 'published_by')
        
        # Admin/HR can see all policies
        if user.role in ['admin', 'hr']:
            return queryset.all()
        
        # For update/delete actions, only Admin/HR can access (handled by permissions)
        # So return empty queryset for non-admin users attempting these actions
        if self.action in ['update', 'partial_update', 'destroy']:
            return queryset.none()
        
        # For retrieve, show only published policies
        if self.action == 'retrieve':
            return queryset.filter(status='published')
        
        # For list view, filter by role - SQLite compatible approach
        queryset = queryset.filter(status='published')
        
        # Get all published policies and filter in Python
        policies = list(queryset)
        filtered_policies = [
            policy for policy in policies
            if not policy.applies_to_roles or user.role in policy.applies_to_roles
        ]
        
        # Return queryset filtered by IDs
        policy_ids = [p.id for p in filtered_policies]
        return queryset.filter(id__in=policy_ids) if policy_ids else queryset.none()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PolicyListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PolicyCreateUpdateSerializer
        return PolicyDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'publish', 'archive']:
            return [IsAuthenticated(), IsAdminOrHR()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrHR])
    def publish(self, request, pk=None):
        """Publish a policy"""
        policy = self.get_object()
        
        if policy.status == 'published':
            return Response(
                {'error': 'Policy is already published'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        policy.status = 'published'
        policy.published_by = request.user
        policy.published_at = timezone.now()
        policy.save()
        
        # Create acknowledgment records for all applicable users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if policy.applies_to_roles:
            users = User.objects.filter(is_active=True, role__in=policy.applies_to_roles)
        else:
            users = User.objects.filter(is_active=True)
        
        for user in users:
            PolicyAcknowledgment.objects.get_or_create(
                policy=policy,
                user=user
            )
        
        serializer = PolicyDetailSerializer(policy, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrHR])
    def archive(self, request, pk=None):
        """Archive a policy"""
        policy = self.get_object()
        policy.status = 'archived'
        policy.save()
        
        serializer = PolicyDetailSerializer(policy, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge a policy"""
        policy = self.get_object()
        
        if policy.status != 'published':
            return Response(
                {'error': 'Only published policies can be acknowledged'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if policy applies to user
        if policy.applies_to_roles and request.user.role not in policy.applies_to_roles:
            return Response(
                {'error': 'This policy does not apply to your role'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = AcknowledgeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create acknowledgment
        acknowledgment, created = PolicyAcknowledgment.objects.get_or_create(
            policy=policy,
            user=request.user
        )
        
        if acknowledgment.acknowledged:
            return Response(
                {'error': 'You have already acknowledged this policy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate signature if required
        if policy.requires_signature and not serializer.validated_data.get('signature'):
            return Response(
                {'error': 'Signature is required for this policy'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update acknowledgment
        acknowledgment.acknowledged = True
        acknowledgment.acknowledged_at = timezone.now()
        acknowledgment.signature = serializer.validated_data.get('signature', '')
        acknowledgment.comments = serializer.validated_data.get('comments', '')
        acknowledgment.ip_address = get_client_ip(request)
        acknowledgment.user_agent = request.META.get('HTTP_USER_AGENT', '')
        acknowledgment.save()
        
        return Response({
            'message': 'Policy acknowledged successfully',
            'policy': policy.title,
            'acknowledged_at': acknowledgment.acknowledged_at
        })
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get policies pending acknowledgment for current user"""
        user = request.user
        
        # Get all published policies
        all_policies = Policy.objects.filter(status='published')
        
        # Filter by role using Python (SQLite compatible)
        if user.role not in ['admin', 'hr']:
            policies = [
                policy for policy in all_policies
                if not policy.applies_to_roles or user.role in policy.applies_to_roles
            ]
        else:
            policies = list(all_policies)
        
        # Filter to only those not yet acknowledged
        pending_policies = []
        for policy in policies:
            try:
                ack = PolicyAcknowledgment.objects.get(policy=policy, user=user)
                if not ack.acknowledged:
                    pending_policies.append(policy)
            except PolicyAcknowledgment.DoesNotExist:
                pending_policies.append(policy)
        
        serializer = PolicyListSerializer(pending_policies, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_compliance(self, request):
        """Get current user's compliance status"""
        user = request.user
        
        # Get all published policies
        all_policies = Policy.objects.filter(status='published')
        
        # Filter by role using Python (SQLite compatible)
        if user.role not in ['admin', 'hr']:
            policies = [
                policy for policy in all_policies
                if not policy.applies_to_roles or user.role in policy.applies_to_roles
            ]
        else:
            policies = list(all_policies)
        
        total_policies = len(policies)
        
        # Count acknowledgments
        acknowledged_count = 0
        pending_count = 0
        overdue_count = 0
        pending_policies_list = []
        
        for policy in policies:
            try:
                ack = PolicyAcknowledgment.objects.get(policy=policy, user=user)
                if ack.acknowledged:
                    acknowledged_count += 1
                else:
                    pending_count += 1
                    pending_policies_list.append(policy)
                    
                    # Check if overdue
                    if policy.published_at:
                        deadline = policy.published_at + timedelta(days=policy.acknowledgment_deadline_days)
                        if timezone.now() > deadline:
                            overdue_count += 1
            except PolicyAcknowledgment.DoesNotExist:
                pending_count += 1
                pending_policies_list.append(policy)
        
        compliance_percentage = (acknowledged_count / total_policies * 100) if total_policies > 0 else 100
        
        data = {
            'total_policies': total_policies,
            'acknowledged_count': acknowledged_count,
            'pending_count': pending_count,
            'overdue_count': overdue_count,
            'compliance_percentage': round(compliance_percentage, 2),
            'pending_policies': pending_policies_list
        }
        
        serializer = ComplianceStatusSerializer(data, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminOrHR])
    def compliance_report(self, request):
        """Get organization-wide compliance report"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = User.objects.filter(is_active=True)
        report_data = []
        
        for user in users:
            # Get all published policies
            all_policies = Policy.objects.filter(status='published')
            
            # Filter by role using Python (SQLite compatible)
            if user.role not in ['admin', 'hr']:
                policies = [
                    policy for policy in all_policies
                    if not policy.applies_to_roles or user.role in policy.applies_to_roles
                ]
            else:
                policies = list(all_policies)
            
            total_policies = len(policies)
            acknowledged_count = 0
            pending_count = 0
            overdue_count = 0
            
            for policy in policies:
                try:
                    ack = PolicyAcknowledgment.objects.get(policy=policy, user=user)
                    if ack.acknowledged:
                        acknowledged_count += 1
                    else:
                        pending_count += 1
                        
                        # Check if overdue
                        if policy.published_at:
                            deadline = policy.published_at + timedelta(days=policy.acknowledgment_deadline_days)
                            if timezone.now() > deadline:
                                overdue_count += 1
                except PolicyAcknowledgment.DoesNotExist:
                    pending_count += 1
            
            compliance_percentage = (acknowledged_count / total_policies * 100) if total_policies > 0 else 100
            
            report_data.append({
                'user_id': user.id,
                'user_name': user.get_full_name(),
                'user_email': user.email,
                'role': user.role,
                'total_policies': total_policies,
                'acknowledged': acknowledged_count,
                'pending': pending_count,
                'overdue': overdue_count,
                'compliance_percentage': round(compliance_percentage, 2)
            })
        
        serializer = UserComplianceReportSerializer(report_data, many=True)
        return Response(serializer.data)


class PolicyAcknowledgmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing policy acknowledgments
    
    Permissions:
    - list, retrieve: Admin/HR only
    """
    queryset = PolicyAcknowledgment.objects.select_related('policy', 'user').all()
    serializer_class = PolicyAcknowledgmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by policy if provided
        policy_id = self.request.query_params.get('policy')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        # Filter by user if provided
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by acknowledged status
        acknowledged = self.request.query_params.get('acknowledged')
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')
        
        return queryset
