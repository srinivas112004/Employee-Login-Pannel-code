from rest_framework import serializers
from django.utils import timezone
from datetime import date
from .models import Leave, LeaveType, LeaveBalance
from authentication.models import User


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'name', 'code', 'default_days', 'description', 
                  'requires_document', 'is_active']


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    
    class Meta:
        model = LeaveBalance
        fields = ['id', 'leave_type', 'leave_type_name', 'leave_type_code',
                  'year', 'total_days', 'used_days', 'available_days']
        read_only_fields = ['used_days', 'available_days']


class LeaveSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    applied_to_email = serializers.EmailField(source='applied_to.email', read_only=True)
    applied_to_name = serializers.SerializerMethodField()
    secondary_approver_email = serializers.EmailField(source='secondary_approver.email', read_only=True)
    secondary_approver_name = serializers.SerializerMethodField()
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True)
    approved_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    next_approver = serializers.SerializerMethodField()
    
    class Meta:
        model = Leave
        fields = [
            'id', 'user', 'user_email', 'user_name', 'leave_type', 
            'leave_type_name', 'start_date', 'end_date', 'total_days',
            'reason', 'status', 'status_display', 'document',
            'applied_to', 'applied_to_email', 'applied_to_name',
            'secondary_approver', 'secondary_approver_email', 'secondary_approver_name',
            'approved_by', 'approved_by_email', 'approved_by_name',
            'approved_at', 'rejection_reason',
            'approval_level', 'current_approval_level', 'requires_multi_level',
            'next_approver', 'notification_sent', 'notification_sent_at',
            'approval_notification_sent', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'total_days', 'approved_by', 'approved_at', 
            'approval_level', 'current_approval_level', 'requires_multi_level',
            'notification_sent', 'notification_sent_at', 'approval_notification_sent',
            'created_at', 'updated_at'
        ]

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
    
    def get_applied_to_name(self, obj):
        if obj.applied_to:
            return f"{obj.applied_to.first_name} {obj.applied_to.last_name}".strip() or obj.applied_to.email
        return None
    
    def get_secondary_approver_name(self, obj):
        if obj.secondary_approver:
            return f"{obj.secondary_approver.first_name} {obj.secondary_approver.last_name}".strip() or obj.secondary_approver.email
        return None
    
    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}".strip() or obj.approved_by.email
        return None
    
    def get_next_approver(self, obj):
        """Get the next approver email"""
        if obj.status == 'pending':
            next_approver = obj.get_next_approver()
            if next_approver:
                return {
                    'id': next_approver.id,
                    'email': next_approver.email,
                    'name': f"{next_approver.first_name} {next_approver.last_name}".strip() or next_approver.email
                }
        return None

    def validate(self, data):
        """
        Validate leave application
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        leave_type = data.get('leave_type')
        
        # Validate dates
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date'
                })
            
            if start_date < date.today():
                raise serializers.ValidationError({
                    'start_date': 'Cannot apply for leave in the past'
                })
        
        # Check for overlapping leaves
        user = self.context['request'].user
        
        overlapping_leaves = Leave.objects.filter(
            user=user,
            status__in=['pending', 'approved'],
            start_date__lte=end_date,
            end_date__gte=start_date
        )
        
        # Exclude current leave if updating
        if self.instance:
            overlapping_leaves = overlapping_leaves.exclude(id=self.instance.id)
        
        if overlapping_leaves.exists():
            raise serializers.ValidationError({
                'dates': 'You have already applied for leave during this period'
            })
        
        # Check if document is required
        if leave_type and leave_type.requires_document:
            if not data.get('document') and not (self.instance and self.instance.document):
                raise serializers.ValidationError({
                    'document': f'{leave_type.name} requires a document to be uploaded'
                })
        
        return data

    def validate_leave_balance(self, user, leave_type, total_days):
        """
        Check if user has sufficient leave balance
        """
        current_year = date.today().year
        
        try:
            balance = LeaveBalance.objects.get(
                user=user,
                leave_type=leave_type,
                year=current_year
            )
            
            if balance.available_days < total_days:
                raise serializers.ValidationError({
                    'leave_type': f'Insufficient leave balance. Available: {balance.available_days} days'
                })
        except LeaveBalance.DoesNotExist:
            raise serializers.ValidationError({
                'leave_type': 'Leave balance not found for this leave type'
            })

    def create(self, validated_data):
        # Set user from request
        validated_data['user'] = self.context['request'].user
        
        # Create leave instance to calculate days
        leave = Leave(**validated_data)
        total_days = leave.calculate_leave_days()
        validated_data['total_days'] = total_days
        
        # Validate balance
        self.validate_leave_balance(
            validated_data['user'],
            validated_data['leave_type'],
            total_days
        )
        
        # Set applied_to (manager of the user)
        user = validated_data['user']
        if hasattr(user, 'manager') and user.manager:
            validated_data['applied_to'] = user.manager
        else:
            # If no manager assigned, find any manager in the system
            from authentication.models import User
            manager = User.objects.filter(role='manager').first()
            if manager:
                validated_data['applied_to'] = manager
        
        # Set secondary approver for multi-level approval (HR or Department Head)
        # If leave > 5 days or special leave types, requires secondary approval
        if total_days > 5 or validated_data['leave_type'].code in ['ML', 'PL']:
            # Find HR or admin for secondary approval
            from authentication.models import User
            hr_user = User.objects.filter(role__in=['hr', 'admin']).first()
            if hr_user:
                validated_data['secondary_approver'] = hr_user
        
        return super().create(validated_data)


class LeaveApprovalSerializer(serializers.Serializer):
    """
    Serializer for approving/rejecting leave
    """
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data['action'] == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({
                'rejection_reason': 'Rejection reason is required when rejecting leave'
            })
        return data


class LeaveCalendarSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for leave calendar view
    """
    user_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    
    class Meta:
        model = Leave
        fields = [
            'id', 'user', 'user_name', 'leave_type_name', 'leave_type_code',
            'start_date', 'end_date', 'total_days', 'status'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class TeamLeaveSerializer(serializers.ModelSerializer):
    """
    Serializer for team leave view (for managers)
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Leave
        fields = [
            'id', 'user_email', 'user_name', 'leave_type_name', 'leave_type_code',
            'start_date', 'end_date', 'total_days', 'status', 'status_display',
            'reason', 'created_at'
        ]
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email
