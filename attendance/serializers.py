from rest_framework import serializers
from django.utils import timezone
from .models import Shift, Attendance, AttendanceRegularization, WorkFromHomeRequest
from authentication.models import User


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ['id', 'name', 'start_time', 'end_time', 'grace_period_minutes', 
                  'total_hours', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class AttendanceSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    user_role = serializers.CharField(source='user.role', read_only=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    regularized_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'user', 'user_email', 'user_name', 'user_role', 'date', 
            'shift', 'shift_name',
            'check_in_time', 'check_in_location', 'check_in_address', 'check_in_ip',
            'check_out_time', 'check_out_location', 'check_out_address', 'check_out_ip',
            'status', 'status_display', 'is_late', 'late_by_minutes',
            'work_hours', 'overtime_hours', 'remarks',
            'is_regularized', 'regularized_by', 'regularized_by_name',
            'regularization_reason', 'regularized_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'work_hours', 'overtime_hours', 'is_late', 
                            'late_by_minutes', 'is_regularized', 'regularized_by',
                            'regularization_reason', 'regularized_at',
                            'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_regularized_by_name(self, obj):
        if obj.regularized_by:
            return f"{obj.regularized_by.first_name} {obj.regularized_by.last_name}".strip() or obj.regularized_by.email
        return None


class CheckInSerializer(serializers.Serializer):
    """Serializer for check-in request"""
    location = serializers.CharField(max_length=255, help_text="Latitude, Longitude")
    address = serializers.CharField(required=False, allow_blank=True)
    shift_id = serializers.IntegerField(required=False)


class CheckOutSerializer(serializers.Serializer):
    """Serializer for check-out request"""
    location = serializers.CharField(max_length=255, help_text="Latitude, Longitude")
    address = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)


class AttendanceRegularizationSerializer(serializers.ModelSerializer):
    requested_by_email = serializers.EmailField(source='requested_by.email', read_only=True)
    requested_by_name = serializers.SerializerMethodField()
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    attendance_date = serializers.DateField(source='attendance.date', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AttendanceRegularization
        fields = [
            'id', 'attendance', 'attendance_date', 'requested_by', 
            'requested_by_email', 'requested_by_name',
            'reason', 'requested_check_in', 'requested_check_out', 'requested_status',
            'status', 'status_display', 'approved_by', 'approved_by_email', 
            'approved_by_name', 'approved_at', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['requested_by', 'approved_by', 'approved_at', 
                            'created_at', 'updated_at']

    def get_requested_by_name(self, obj):
        return f"{obj.requested_by.first_name} {obj.requested_by.last_name}".strip() or obj.requested_by.email

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}".strip() or obj.approved_by.email
        return None

    def validate(self, data):
        """Validate regularization request"""
        if data.get('status') == 'approved':
            if not data.get('requested_check_in') and not data.get('requested_check_out') and not data.get('requested_status'):
                raise serializers.ValidationError(
                    "At least one field (check_in, check_out, or status) must be provided for regularization."
                )
        return data


class WorkFromHomeRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = WorkFromHomeRequest
        fields = [
            'id', 'user', 'user_email', 'user_name', 'date', 'reason',
            'status', 'status_display', 'approved_by', 'approved_by_email',
            'approved_by_name', 'approved_at', 'rejection_reason',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}".strip() or obj.approved_by.email
        return None

    def validate_date(self, value):
        """Validate WFH date"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Cannot request WFH for past dates.")
        return value


class AttendanceSummarySerializer(serializers.Serializer):
    """Monthly attendance summary"""
    total_days = serializers.IntegerField()
    present_days = serializers.IntegerField()
    absent_days = serializers.IntegerField()
    half_days = serializers.IntegerField()
    leaves = serializers.IntegerField()
    wfh_days = serializers.IntegerField()
    late_count = serializers.IntegerField()
    total_work_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    total_overtime = serializers.DecimalField(max_digits=6, decimal_places=2)
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
