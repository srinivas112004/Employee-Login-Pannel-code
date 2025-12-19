from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, timedelta, date
from .models import Shift, Attendance, AttendanceRegularization, WorkFromHomeRequest
from .serializers import (
    ShiftSerializer, AttendanceSerializer, CheckInSerializer, CheckOutSerializer,
    AttendanceRegularizationSerializer, WorkFromHomeRequestSerializer,
    AttendanceSummarySerializer
)
from authentication.permissions import IsManager, IsManagerOrAbove


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class ShiftViewSet(viewsets.ModelViewSet):
    """Shift management endpoints"""
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Only managers can create/update/delete shifts"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsManagerOrAbove()]
        return [IsAuthenticated()]


class AttendanceViewSet(viewsets.ModelViewSet):
    """Attendance management endpoints"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter attendance based on user role"""
        user = self.request.user
        if user.role in ['admin', 'hr', 'manager']:
            return Attendance.objects.all()
        return Attendance.objects.filter(user=user)

    @action(detail=False, methods=['post'], url_path='checkin')
    def checkin(self, request):
        """Check in for the day"""
        serializer = CheckInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        # Check if already checked in today
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing and existing.check_in_time:
            return Response(
                {'error': 'Already checked in today', 'attendance': AttendanceSerializer(existing).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get shift
        shift_id = serializer.validated_data.get('shift_id')
        shift = None
        if shift_id:
            shift = Shift.objects.filter(id=shift_id, is_active=True).first()

        # Create or update attendance
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'shift': shift,
                'check_in_time': timezone.now(),
                'check_in_location': serializer.validated_data['location'],
                'check_in_address': serializer.validated_data.get('address', ''),
                'check_in_ip': get_client_ip(request),
                'status': 'present'
            }
        )

        if not created:
            attendance.check_in_time = timezone.now()
            attendance.check_in_location = serializer.validated_data['location']
            attendance.check_in_address = serializer.validated_data.get('address', '')
            attendance.check_in_ip = get_client_ip(request)
            if shift:
                attendance.shift = shift
            attendance.save()

        return Response(
            {
                'message': 'Checked in successfully',
                'attendance': AttendanceSerializer(attendance).data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """Check out for the day"""
        serializer = CheckOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        # Get today's attendance
        try:
            attendance = Attendance.objects.get(user=user, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No check-in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not attendance.check_in_time:
            return Response(
                {'error': 'You must check in first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if attendance.check_out_time:
            return Response(
                {'error': 'Already checked out', 'attendance': AttendanceSerializer(attendance).data},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update checkout details
        attendance.check_out_time = timezone.now()
        attendance.check_out_location = serializer.validated_data['location']
        attendance.check_out_address = serializer.validated_data.get('address', '')
        attendance.check_out_ip = get_client_ip(request)
        attendance.remarks = serializer.validated_data.get('remarks', '')
        attendance.save()

        return Response(
            {
                'message': 'Checked out successfully',
                'attendance': AttendanceSerializer(attendance).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='my-records')
    def my_records(self, request):
        """Get my attendance records"""
        # Get query parameters
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        queryset = Attendance.objects.filter(user=request.user)
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
        
        queryset = queryset.order_by('-date')
        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='today-status')
    def today_status(self, request):
        """Get today's attendance status"""
        today = timezone.now().date()
        try:
            attendance = Attendance.objects.get(user=request.user, date=today)
            return Response(AttendanceSerializer(attendance).data, status=status.HTTP_200_OK)
        except Attendance.DoesNotExist:
            return Response({
                'message': 'No attendance record for today',
                'date': str(today),
                'checked_in': False
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request):
        """Get monthly attendance summary"""
        month = request.query_params.get('month', timezone.now().month)
        year = request.query_params.get('year', timezone.now().year)
        
        user = request.user
        
        # Get all attendance for the month
        records = Attendance.objects.filter(
            user=user,
            date__month=month,
            date__year=year
        )
        
        # Calculate summary
        total_days = records.count()
        present_days = records.filter(status='present').count()
        absent_days = records.filter(status='absent').count()
        half_days = records.filter(status='half_day').count()
        leaves = records.filter(status='on_leave').count()
        wfh_days = records.filter(status='work_from_home').count()
        late_count = records.filter(is_late=True).count()
        
        total_work_hours = records.aggregate(total=Sum('work_hours'))['total'] or 0
        total_overtime = records.aggregate(total=Sum('overtime_hours'))['total'] or 0
        
        # Calculate working days in month
        import calendar
        working_days = sum(1 for day in calendar.monthcalendar(int(year), int(month))
                          if day[0] != 0 and day[6] == 0)  # Exclude Sundays
        
        attendance_percentage = (present_days / working_days * 100) if working_days > 0 else 0
        
        summary = {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'half_days': half_days,
            'leaves': leaves,
            'wfh_days': wfh_days,
            'late_count': late_count,
            'total_work_hours': round(total_work_hours, 2),
            'total_overtime': round(total_overtime, 2),
            'attendance_percentage': round(attendance_percentage, 2)
        }
        
        serializer = AttendanceSummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='late-records')
    def late_records(self, request):
        """Get late coming records"""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        queryset = Attendance.objects.filter(user=request.user, is_late=True)
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        
        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='overtime-records')
    def overtime_records(self, request):
        """Get overtime records"""
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        queryset = Attendance.objects.filter(user=request.user, overtime_hours__gt=0)
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        
        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)


class AttendanceRegularizationViewSet(viewsets.ModelViewSet):
    """Attendance regularization endpoints"""
    serializer_class = AttendanceRegularizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if user.role in ['admin', 'hr', 'manager']:
            return AttendanceRegularization.objects.all()
        return AttendanceRegularization.objects.filter(requested_by=user)

    def perform_create(self, serializer):
        """Set requested_by to current user"""
        serializer.save(requested_by=self.request.user)

    @action(detail=False, methods=['get'], permission_classes=[IsManagerOrAbove], url_path='pending-requests')
    def pending_requests(self, request):
        """Get pending regularization requests (Manager/HR/Admin only)"""
        pending = AttendanceRegularization.objects.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def approve(self, request, pk=None):
        """Approve regularization request"""
        regularization = self.get_object()
        
        if regularization.status != 'pending':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update regularization
        regularization.status = 'approved'
        regularization.approved_by = request.user
        regularization.approved_at = timezone.now()
        regularization.save()
        
        # Update attendance record
        attendance = regularization.attendance
        if regularization.requested_check_in:
            attendance.check_in_time = regularization.requested_check_in
        if regularization.requested_check_out:
            attendance.check_out_time = regularization.requested_check_out
        if regularization.requested_status:
            attendance.status = regularization.requested_status
        
        attendance.is_regularized = True
        attendance.regularized_by = request.user
        attendance.regularization_reason = regularization.reason
        attendance.regularized_at = timezone.now()
        attendance.save()
        
        return Response(
            {
                'message': 'Regularization approved successfully',
                'regularization': self.get_serializer(regularization).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def reject(self, request, pk=None):
        """Reject regularization request"""
        regularization = self.get_object()
        
        if regularization.status != 'pending':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        regularization.status = 'rejected'
        regularization.approved_by = request.user
        regularization.approved_at = timezone.now()
        regularization.rejection_reason = rejection_reason
        regularization.save()
        
        return Response(
            {
                'message': 'Regularization rejected',
                'regularization': self.get_serializer(regularization).data
            },
            status=status.HTTP_200_OK
        )


class WorkFromHomeRequestViewSet(viewsets.ModelViewSet):
    """Work from home request endpoints"""
    serializer_class = WorkFromHomeRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if user.role in ['admin', 'hr', 'manager']:
            return WorkFromHomeRequest.objects.all()
        return WorkFromHomeRequest.objects.filter(user=user)

    def perform_create(self, serializer):
        """Set user to current user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='my')
    def my_wfh_requests(self, request):
        """Get current user's WFH requests"""
        wfh_requests = WorkFromHomeRequest.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(wfh_requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsManagerOrAbove], url_path='pending-requests')
    def pending_requests(self, request):
        """Get pending WFH requests (Manager/HR/Admin only)"""
        pending = WorkFromHomeRequest.objects.filter(status='pending')
        serializer = self.get_serializer(pending, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def approve(self, request, pk=None):
        """Approve WFH request"""
        wfh_request = self.get_object()
        
        if wfh_request.status != 'pending':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        wfh_request.status = 'approved'
        wfh_request.approved_by = request.user
        wfh_request.approved_at = timezone.now()
        wfh_request.save()
        
        # Update or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            user=wfh_request.user,
            date=wfh_request.date,
            defaults={'status': 'work_from_home'}
        )
        
        if not created:
            attendance.status = 'work_from_home'
            attendance.save()
        
        return Response(
            {
                'message': 'WFH request approved successfully',
                'wfh_request': self.get_serializer(wfh_request).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsManagerOrAbove])
    def reject(self, request, pk=None):
        """Reject WFH request"""
        wfh_request = self.get_object()
        
        if wfh_request.status != 'pending':
            return Response(
                {'error': 'This request has already been processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason', '')
        
        wfh_request.status = 'rejected'
        wfh_request.approved_by = request.user
        wfh_request.approved_at = timezone.now()
        wfh_request.rejection_reason = rejection_reason
        wfh_request.save()
        
        return Response(
            {
                'message': 'WFH request rejected',
                'wfh_request': self.get_serializer(wfh_request).data
            },
            status=status.HTTP_200_OK
        )
