from rest_framework import serializers
from django.utils import timezone
from .models import EmployeeProfile, EmployeeDocument, OnboardingChecklist, EmploymentHistory
from authentication.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role']


class EmploymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for employment history"""
    class Meta:
        model = EmploymentHistory
        fields = [
            'id', 'employee', 'company_name', 'designation', 
            'start_date', 'end_date', 'is_current', 
            'job_description', 'reason_for_leaving',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OnboardingChecklistSerializer(serializers.ModelSerializer):
    """Serializer for onboarding checklist"""
    assigned_to_name = serializers.SerializerMethodField()
    completed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OnboardingChecklist
        fields = [
            'id', 'employee', 'task_name', 'task_description', 
            'status', 'assigned_to', 'assigned_to_name',
            'completed_by', 'completed_by_name', 'completed_at',
            'due_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'completed_by', 'completed_at']
    
    def get_assigned_to_name(self, obj):
        return obj.assigned_to.email if obj.assigned_to else None
    
    def get_completed_by_name(self, obj):
        return obj.completed_by.email if obj.completed_by else None


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    """Serializer for employee documents"""
    verified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeDocument
        fields = [
            'id', 'employee', 'document_type', 'document_file',
            'is_verified', 'verified_by', 'verified_by_name',
            'verified_at', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['uploaded_at', 'updated_at', 'is_verified', 'verified_by', 'verified_at']
    
    def get_verified_by_name(self, obj):
        return obj.verified_by.email if obj.verified_by else None


class EmployeeProfileSerializer(serializers.ModelSerializer):
    """Serializer for employee profile with nested data"""
    user = UserBasicSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    reporting_manager_name = serializers.SerializerMethodField()
    documents = EmployeeDocumentSerializer(many=True, read_only=True)
    onboarding_tasks = OnboardingChecklistSerializer(many=True, read_only=True)
    employment_history = EmploymentHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'user_id', 'reporting_manager', 'reporting_manager_name',
            'employee_id', 'designation', 'department', 'joining_date',
            'date_of_birth', 'gender', 'marital_status', 'blood_group',
            'phone_primary', 'phone_secondary', 'email_personal',
            'current_address', 'permanent_address',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'bank_account_number', 'bank_name', 'bank_ifsc_code', 
            'pan_number', 'aadhaar_number',
            'profile_picture', 'onboarding_completed', 'onboarding_completed_date',
            'documents', 'onboarding_tasks', 'employment_history',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'onboarding_completed_date']
    
    def get_reporting_manager_name(self, obj):
        return obj.reporting_manager.email if obj.reporting_manager else None
    
    def create(self, validated_data):
        """Create employee profile with user assignment"""
        user_id = validated_data.pop('user_id', None)
        
        # If user_id not provided, use the current logged-in user
        if not user_id:
            user_id = self.context['request'].user.id
        
        # Get the user object
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({'user_id': 'User not found'})
        
        # Check if user already has a profile
        if hasattr(user, 'employee_profile'):
            raise serializers.ValidationError({'user_id': 'This user already has an employee profile'})
        
        # Create the profile
        validated_data['user'] = user
        return super().create(validated_data)


class EmployeeProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing employees"""
    user = UserBasicSerializer(read_only=True)
    reporting_manager_name = serializers.SerializerMethodField()
    
    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'user', 'employee_id', 'designation', 'department',
            'joining_date', 'phone_primary', 'email_personal',
            'reporting_manager_name', 'onboarding_completed',
            'created_at'
        ]
    
    def get_reporting_manager_name(self, obj):
        return obj.reporting_manager.email if obj.reporting_manager else None
