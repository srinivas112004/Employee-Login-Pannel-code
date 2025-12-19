"""
Serializers for Activity Logs and Audit Trail
"""

from rest_framework import serializers
from datetime import datetime


class ActivityLogSerializer(serializers.Serializer):
    """Serializer for Activity Log entries"""
    id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField()
    user_id = serializers.IntegerField(allow_null=True)
    user_email = serializers.EmailField(allow_null=True)
    user_name = serializers.CharField(allow_null=True)
    action = serializers.CharField()
    method = serializers.CharField()
    endpoint = serializers.CharField()
    ip_address = serializers.IPAddressField(allow_null=True)
    user_agent = serializers.CharField(allow_null=True)
    status_code = serializers.IntegerField()
    response_time = serializers.IntegerField(allow_null=True, help_text="Response time in milliseconds")
    request_data = serializers.JSONField(allow_null=True)
    response_data = serializers.JSONField(allow_null=True)
    error_message = serializers.CharField(allow_null=True)
    model_name = serializers.CharField(allow_null=True)
    object_id = serializers.CharField(allow_null=True)
    changes = serializers.JSONField(allow_null=True)
    metadata = serializers.JSONField(allow_null=True)


class AuditLogSerializer(serializers.Serializer):
    """Serializer for Audit Trail (CRUD operations only)"""
    id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField()
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    action = serializers.CharField()
    model_name = serializers.CharField()
    object_id = serializers.CharField()
    changes = serializers.JSONField(allow_null=True)
    endpoint = serializers.CharField()
    ip_address = serializers.IPAddressField()


class ActivityLogFilterSerializer(serializers.Serializer):
    """Serializer for activity log filters"""
    user_id = serializers.IntegerField(required=False)
    action = serializers.ChoiceField(
        choices=['CREATE', 'READ', 'UPDATE', 'DELETE'],
        required=False
    )
    method = serializers.ChoiceField(
        choices=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
        required=False
    )
    model_name = serializers.CharField(required=False)
    object_id = serializers.CharField(required=False)
    status_code = serializers.IntegerField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    search = serializers.CharField(required=False)
    page = serializers.IntegerField(default=1, min_value=1)
    page_size = serializers.IntegerField(default=50, min_value=1, max_value=200)
    
    def validate(self, data):
        """Validate filter data"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("start_date must be before end_date")
        return data


class ActivityLogStatsSerializer(serializers.Serializer):
    """Serializer for activity log statistics"""
    total_logs = serializers.IntegerField()
    total_users = serializers.IntegerField()
    actions_breakdown = serializers.DictField()
    status_codes_breakdown = serializers.DictField()
    top_endpoints = serializers.ListField()
    top_users = serializers.ListField()
    recent_errors = serializers.ListField()
    average_response_time = serializers.FloatField()
