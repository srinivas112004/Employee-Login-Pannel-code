"""
Serializers for Document Management System
"""

from rest_framework import serializers
from .models import (
    DocumentCategory, Document, DocumentVersion,
    DocumentAccess, DocumentShare
)
from django.contrib.auth import get_user_model

User = get_user_model()


class DocumentCategorySerializer(serializers.ModelSerializer):
    """Serializer for document categories"""
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = ['id', 'name', 'description', 'icon', 'document_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_document_count(self, obj):
        return obj.documents.filter(status='active').count()


class DocumentVersionSerializer(serializers.ModelSerializer):
    """Serializer for document versions"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVersion
        fields = [
            'id', 'version_number', 'file', 'file_url', 'file_name', 
            'file_size', 'change_summary', 'uploaded_by', 
            'uploaded_by_name', 'created_at'
        ]
        read_only_fields = ['uploaded_by', 'created_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for document listings"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    file_extension = serializers.SerializerMethodField()
    user_can_access = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'file_name', 'file_size', 'file_type', 'file_extension',
            'current_version', 'access_level', 'status',
            'uploaded_by', 'uploaded_by_name', 'department',
            'tags', 'download_count', 'view_count',
            'created_at', 'updated_at', 'user_can_access'
        ]
        read_only_fields = ['uploaded_by', 'created_at', 'updated_at', 'download_count', 'view_count']
    
    def get_file_extension(self, obj):
        return obj.get_file_extension()
    
    def get_user_can_access(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Admin/HR can access everything
        if user.role in ['admin', 'hr']:
            return True
        
        # Owner can always access
        if obj.uploaded_by == user:
            return True
        
        # Check access level
        if obj.access_level == 'company':
            return True
        elif obj.access_level == 'department':
            return obj.department == user.department
        elif obj.access_level == 'team':
            # Check if user is in allowed_users or has correct role
            if user in obj.allowed_users.all():
                return True
            if obj.allowed_roles and user.role in obj.allowed_roles:
                return True
        elif obj.access_level == 'private':
            return user in obj.allowed_users.all()
        
        return False


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single document view"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    file_url = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    versions = DocumentVersionSerializer(many=True, read_only=True)
    user_can_access = serializers.SerializerMethodField()
    user_can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'category_name',
            'file', 'file_url', 'file_name', 'file_size', 'file_type', 'file_extension',
            'current_version', 'access_level', 'allowed_roles', 'status',
            'uploaded_by', 'uploaded_by_name', 'uploaded_by_email',
            'department', 'tags', 'download_count', 'view_count',
            'created_at', 'updated_at', 'archived_at',
            'versions', 'user_can_access', 'user_can_edit'
        ]
        read_only_fields = [
            'uploaded_by', 'created_at', 'updated_at', 'archived_at',
            'download_count', 'view_count', 'current_version'
        ]
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url'):
            if request is not None:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_extension(self, obj):
        return obj.get_file_extension()
    
    def get_user_can_access(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return self._check_access(obj, request.user)
    
    def get_user_can_edit(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        user = request.user
        return user.role in ['admin', 'hr'] or obj.uploaded_by == user
    
    def _check_access(self, obj, user):
        """Check if user can access document"""
        if user.role in ['admin', 'hr']:
            return True
        if obj.uploaded_by == user:
            return True
        if obj.access_level == 'company':
            return True
        elif obj.access_level == 'department':
            return obj.department == user.department
        elif obj.access_level == 'team':
            if user in obj.allowed_users.all():
                return True
            if obj.allowed_roles and user.role in obj.allowed_roles:
                return True
        elif obj.access_level == 'private':
            return user in obj.allowed_users.all()
        return False


class JSONStringOrListField(serializers.ListField):
    """Custom field that accepts either a list or a JSON string representation of a list"""
    
    def to_internal_value(self, data):
        import json
        
        # Handle the case where multipart/form-data wraps the value in a list
        # e.g., ['[1,2,3]'] instead of '[1,2,3]'
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], str):
            data = data[0]
        
        # If it's a string, try to parse it as JSON
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError, TypeError):
                self.fail('invalid', input=data)
        
        # Now let the parent ListField handle the validation
        return super().to_internal_value(data)


class JSONStringOrJSONField(serializers.JSONField):
    """Custom field that accepts either a dict/list or a JSON string or comma-separated string"""
    
    def to_internal_value(self, data):
        import json
        
        # Handle the case where multipart/form-data wraps the value in a list
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], str):
            data = data[0]
        
        # If it's a string, try to parse it as JSON first
        if isinstance(data, str):
            # First try JSON parsing
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError, TypeError):
                # If not JSON, treat as comma-separated string
                if data.strip():
                    data = [tag.strip() for tag in data.split(',') if tag.strip()]
                else:
                    data = []
        
        # Now let the parent JSONField handle the validation
        return super().to_internal_value(data)


class DocumentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating documents"""
    allowed_user_ids = JSONStringOrListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    allowed_roles = JSONStringOrListField(
        child=serializers.CharField(),
        required=False
    )
    tags = JSONStringOrJSONField(
        required=False
    )
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'category', 'file',
            'access_level', 'allowed_roles', 'allowed_user_ids',
            'status', 'department', 'tags'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'file': {'required': False}  # File is optional for updates
        }
    
    def validate_file(self, value):
        """Validate file size and type"""
        # Max file size: 50MB
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 50MB")
        return value
    
    def validate_allowed_roles(self, value):
        """Validate role list"""
        if value:
            valid_roles = ['admin', 'hr', 'manager', 'employee', 'intern']
            for role in value:
                if role not in valid_roles:
                    raise serializers.ValidationError(f"Invalid role: {role}")
        return value
    
    def create(self, validated_data):
        """Create new document"""
        allowed_user_ids = validated_data.pop('allowed_user_ids', [])
        file = validated_data.get('file')
        
        if not file:
            raise serializers.ValidationError({'file': 'A file is required when creating a document.'})
        
        # Extract file information
        validated_data['file_name'] = file.name
        validated_data['file_size'] = file.size
        validated_data['file_type'] = file.content_type
        validated_data['uploaded_by'] = self.context['request'].user
        
        document = Document.objects.create(**validated_data)
        
        # Add allowed users
        if allowed_user_ids:
            users = User.objects.filter(id__in=allowed_user_ids)
            document.allowed_users.set(users)
        
        # Create initial version
        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=file,
            file_name=file.name,
            file_size=file.size,
            uploaded_by=self.context['request'].user,
            change_summary="Initial version"
        )
        
        return document
    
    def update(self, instance, validated_data):
        """Update document"""
        allowed_user_ids = validated_data.pop('allowed_user_ids', None)
        file = validated_data.get('file')
        
        # If new file uploaded, create new version
        if file:
            instance.current_version += 1
            validated_data['file_name'] = file.name
            validated_data['file_size'] = file.size
            validated_data['file_type'] = file.content_type
            
            # Create new version
            DocumentVersion.objects.create(
                document=instance,
                version_number=instance.current_version,
                file=file,
                file_name=file.name,
                file_size=file.size,
                uploaded_by=self.context['request'].user,
                change_summary=validated_data.get('change_summary', 'Updated version')
            )
        
        # Update allowed users if provided
        if allowed_user_ids is not None:
            users = User.objects.filter(id__in=allowed_user_ids)
            instance.allowed_users.set(users)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class DocumentAccessSerializer(serializers.ModelSerializer):
    """Serializer for document access logs"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    
    class Meta:
        model = DocumentAccess
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'action', 'version_number', 'ip_address', 'user_agent',
            'accessed_at'
        ]
        read_only_fields = ['accessed_at']


class DocumentShareSerializer(serializers.ModelSerializer):
    """Serializer for document sharing"""
    shared_by_name = serializers.CharField(source='shared_by.get_full_name', read_only=True)
    shared_with_name = serializers.CharField(source='shared_with.get_full_name', read_only=True)
    document_title = serializers.CharField(source='document.title', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentShare
        fields = [
            'id', 'document', 'document_title', 'shared_by', 'shared_by_name',
            'shared_with', 'shared_with_name', 'can_download', 'can_reshare',
            'expires_at', 'message', 'created_at', 'accessed', 'accessed_at',
            'is_expired'
        ]
        read_only_fields = ['document', 'shared_by', 'created_at', 'accessed', 'accessed_at']
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def create(self, validated_data):
        """Create document share"""
        validated_data['shared_by'] = self.context['request'].user
        return super().create(validated_data)
