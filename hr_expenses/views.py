# hr_expenses/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import ExpenseCategory, ExpenseClaim, Receipt, ReimbursementHistory
from .serializers import (
    ExpenseCategorySerializer, ExpenseClaimSerializer,
    ExpenseClaimListSerializer, ReceiptSerializer,
    ReimbursementHistorySerializer, ExpenseClaimSubmissionSerializer,
    ExpenseClaimApprovalSerializer, ReimbursementProcessSerializer
)
from hr_profile.models import EmployeeProfile

User = get_user_model()


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for expense categories
    - Admin/HR: Full CRUD access
    - Others: Read-only (active categories)
    """
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin/HR can see all categories
        if user.role in ['admin', 'hr']:
            return ExpenseCategory.objects.all()
        
        # Others can only see active categories
        return ExpenseCategory.objects.filter(is_active=True)
    
    def create(self, request, *args, **kwargs):
        """Create expense category - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can create expense categories.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        """Update expense category - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can update expense categories.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete expense category - Admin only"""
        if request.user.role != 'admin':
            return Response(
                {'detail': 'Only Admin can delete expense categories.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class ExpenseClaimViewSet(viewsets.ModelViewSet):
    """
    ViewSet for expense claim management
    - Employees: Create and view own claims
    - Managers: View team claims and approve
    - Admin/HR: Full access
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ExpenseClaimListSerializer
        return ExpenseClaimSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin/HR can see all claims
        if user.role in ['admin', 'hr']:
            queryset = ExpenseClaim.objects.all()
        elif user.role == 'manager':
            # Managers see their own + subordinates' claims
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                subordinates = EmployeeProfile.objects.filter(reporting_manager=user)
                queryset = ExpenseClaim.objects.filter(
                    Q(employee=employee_profile) | Q(employee__in=subordinates)
                )
            except EmployeeProfile.DoesNotExist:
                queryset = ExpenseClaim.objects.none()
        else:
            # Employees see only their own claims
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = ExpenseClaim.objects.filter(employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = ExpenseClaim.objects.none()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by category
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(expense_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(expense_date__lte=date_to)
        
        return queryset.select_related(
            'employee', 'category', 'reviewer', 'reimbursed_by'
        ).prefetch_related('receipts')
    
    def create(self, request, *args, **kwargs):
        """Create expense claim"""
        try:
            employee_profile = EmployeeProfile.objects.get(user=request.user)
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'detail': 'Employee profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(employee=employee_profile)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Update expense claim - only in DRAFT status"""
        claim = self.get_object()
        
        # Only owner can update, and only if in DRAFT status
        if claim.employee.user != request.user:
            if request.user.role not in ['admin', 'hr']:
                return Response(
                    {'detail': 'You can only update your own claims.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        if claim.status != 'DRAFT' and request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only DRAFT claims can be updated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit expense claim for approval"""
        claim = self.get_object()
        
        # Check ownership
        if claim.employee.user != request.user:
            return Response(
                {'detail': 'You can only submit your own claims.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check status
        if claim.status != 'DRAFT':
            return Response(
                {'detail': 'Only DRAFT claims can be submitted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if receipts are required
        if claim.category.requires_receipt and not claim.has_receipts:
            return Response(
                {'detail': 'Receipt is required for this category.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assign reviewer (reporting manager or admin)
        reviewer = None
        if claim.employee.reporting_manager:
            reviewer = claim.employee.reporting_manager
        else:
            # Assign to first admin if no manager
            reviewer = User.objects.filter(role='admin').first()

        if not reviewer:
            return Response(
                {'detail': 'No reviewer available. Please contact the administrator.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        claim.status = 'SUBMITTED'
        claim.submitted_at = timezone.now()
        claim.reviewer = reviewer
        claim.save()
        
        # Create history entry
        ReimbursementHistory.objects.create(
            claim=claim,
            previous_status='DRAFT',
            new_status='SUBMITTED',
            action_by=request.user,
            notes=request.data.get('notes', '')
        )
        
        serializer = self.get_serializer(claim)
        return Response({
            'message': 'Expense claim submitted successfully',
            'claim': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve expense claim - Manager/Admin/HR only"""
        if request.user.role not in ['admin', 'hr', 'manager']:
            return Response(
                {'detail': 'Only managers/admin/HR can approve claims.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        
        # Check if user is the assigned reviewer
        if claim.reviewer != request.user and request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'You are not authorized to approve this claim.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check status
        if claim.status not in ['SUBMITTED', 'UNDER_REVIEW']:
            return Response(
                {'detail': 'Only SUBMITTED or UNDER_REVIEW claims can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ExpenseClaimApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action = serializer.validated_data['action']
        review_notes = serializer.validated_data.get('review_notes', '')
        adjusted_amount = serializer.validated_data.get('adjusted_amount')
        
        previous_status = claim.status
        previous_amount = claim.amount
        
        if action == 'APPROVE':
            claim.status = 'APPROVED'
            if adjusted_amount:
                claim.amount = adjusted_amount
        else:
            claim.status = 'REJECTED'
        
        claim.reviewer = request.user
        claim.reviewed_at = timezone.now()
        claim.review_notes = review_notes
        claim.save()
        
        # Create history entry
        ReimbursementHistory.objects.create(
            claim=claim,
            previous_status=previous_status,
            new_status=claim.status,
            action_by=request.user,
            notes=review_notes,
            previous_amount=previous_amount if adjusted_amount else None,
            new_amount=adjusted_amount
        )
        
        claim_serializer = self.get_serializer(claim)
        return Response({
            'message': f'Expense claim {action.lower()}d successfully',
            'claim': claim_serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_reimbursed(self, request, pk=None):
        """Mark claim as reimbursed - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can mark claims as reimbursed.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        claim = self.get_object()
        
        # Check status
        if claim.status != 'APPROVED':
            return Response(
                {'detail': 'Only APPROVED claims can be reimbursed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReimbursementProcessSerializer(data=request.data, context={'claim': claim})
        serializer.is_valid(raise_exception=True)
        
        claim.status = 'REIMBURSED'
        claim.reimbursement_mode = serializer.validated_data['reimbursement_mode']
        claim.reimbursement_date = serializer.validated_data['reimbursement_date']
        claim.reimbursement_reference = serializer.validated_data['reimbursement_reference']
        claim.reimbursed_by = request.user
        claim.save()
        
        # Create history entry
        ReimbursementHistory.objects.create(
            claim=claim,
            previous_status='APPROVED',
            new_status='REIMBURSED',
            action_by=request.user,
            notes=serializer.validated_data.get('notes', '')
        )
        
        claim_serializer = self.get_serializer(claim)
        return Response({
            'message': 'Claim marked as reimbursed successfully',
            'claim': claim_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def my_claims(self, request):
        """Get current user's expense claims"""
        try:
            employee_profile = EmployeeProfile.objects.get(user=request.user)
            claims = ExpenseClaim.objects.filter(employee=employee_profile)
            
            # Apply status filter
            status_filter = request.query_params.get('status', None)
            if status_filter:
                claims = claims.filter(status=status_filter)
            
            serializer = ExpenseClaimListSerializer(claims, many=True)
            return Response(serializer.data)
            
        except EmployeeProfile.DoesNotExist:
            return Response(
                {'detail': 'Employee profile not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get claims pending approval - Manager/Admin/HR only"""
        if request.user.role not in ['admin', 'hr', 'manager']:
            return Response(
                {'detail': 'Only managers/admin/HR can view pending approvals.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get claims assigned to this user
        claims = ExpenseClaim.objects.filter(
            reviewer=request.user,
            status__in=['SUBMITTED', 'UNDER_REVIEW']
        )
        
        serializer = ExpenseClaimListSerializer(claims, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get expense statistics - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can view statistics.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        stats = {
            'total_claims': ExpenseClaim.objects.count(),
            'pending_claims': ExpenseClaim.objects.filter(status='SUBMITTED').count(),
            'approved_claims': ExpenseClaim.objects.filter(status='APPROVED').count(),
            'rejected_claims': ExpenseClaim.objects.filter(status='REJECTED').count(),
            'reimbursed_claims': ExpenseClaim.objects.filter(status='REIMBURSED').count(),
            'total_amount_claimed': ExpenseClaim.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0,
            'total_amount_approved': ExpenseClaim.objects.filter(
                status__in=['APPROVED', 'REIMBURSED']
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'total_amount_reimbursed': ExpenseClaim.objects.filter(
                status='REIMBURSED'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        return Response(stats)


class ReceiptViewSet(viewsets.ModelViewSet):
    """
    ViewSet for receipt management
    - Upload receipts for claims
    - Verify receipts (Admin/HR)
    """
    serializer_class = ReceiptSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin/HR can see all receipts
        if user.role in ['admin', 'hr']:
            queryset = Receipt.objects.all()
        else:
            # Others see only receipts for their accessible claims
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = Receipt.objects.filter(claim__employee=employee_profile)
            except EmployeeProfile.DoesNotExist:
                queryset = Receipt.objects.none()
        
        # Filter by claim
        claim_id = self.request.query_params.get('claim', None)
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)
        
        return queryset.select_related('claim', 'uploaded_by', 'verified_by')
    
    def create(self, request, *args, **kwargs):
        """Upload receipt for a claim"""
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'detail': 'File is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save with file metadata
        serializer.save(
            uploaded_by=request.user,
            file_name=file.name,
            file_size=file.size,
            file_type=file.content_type
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify receipt - Admin/HR only"""
        if request.user.role not in ['admin', 'hr']:
            return Response(
                {'detail': 'Only Admin/HR can verify receipts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        receipt = self.get_object()
        
        receipt.is_verified = True
        receipt.verified_by = request.user
        receipt.verified_at = timezone.now()
        receipt.verification_notes = request.data.get('verification_notes', '')
        receipt.save()
        
        serializer = self.get_serializer(receipt)
        return Response({
            'message': 'Receipt verified successfully',
            'receipt': serializer.data
        })


class ReimbursementHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for reimbursement history (read-only)
    """
    serializer_class = ReimbursementHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin/HR can see all history
        if user.role in ['admin', 'hr']:
            queryset = ReimbursementHistory.objects.all()
        else:
            # Others see only history for their accessible claims
            try:
                employee_profile = EmployeeProfile.objects.get(user=user)
                queryset = ReimbursementHistory.objects.filter(
                    claim__employee=employee_profile
                )
            except EmployeeProfile.DoesNotExist:
                queryset = ReimbursementHistory.objects.none()
        
        # Filter by claim
        claim_id = self.request.query_params.get('claim', None)
        if claim_id:
            queryset = queryset.filter(claim_id=claim_id)
        
        return queryset.select_related('claim', 'action_by')
