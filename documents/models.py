"""
Models for Document Management System
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import os

User = get_user_model()


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    # documents/user_id/category/filename
    return f'documents/{instance.uploaded_by.id}/{instance.category}/{filename}'


def version_upload_path(instance, filename):
    """Generate upload path for document versions"""
    # documents/versions/document_id/version_number/filename
    return f'documents/versions/{instance.document.id}/v{instance.version_number}/{filename}'


class DocumentCategory(models.Model):
    """Categories for organizing documents"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name for UI")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Document Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """Main document model with versioning support"""
    
    ACCESS_LEVEL_CHOICES = [
        ('private', 'Private'),
        ('team', 'Team'),
        ('department', 'Department'),
        ('company', 'Company-wide'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents'
    )
    
    # File Information
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    file_type = models.CharField(max_length=100)
    
    # Version Information
    current_version = models.IntegerField(default=1)
    
    # Access Control
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='private'
    )
    allowed_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="Roles that can access this document"
    )
    allowed_users = models.ManyToManyField(
        User,
        related_name='accessible_documents',
        blank=True,
        help_text="Specific users who can access this document"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Metadata
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    department = models.CharField(max_length=100, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    download_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploaded_by', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['access_level']),
        ]
    
    def __str__(self):
        return f"{self.title} (v{self.current_version})"
    
    def get_file_extension(self):
        """Get file extension from filename"""
        return os.path.splitext(self.file_name)[1].lower()
    
    def increment_download_count(self):
        """Increment download counter"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def increment_view_count(self):
        """Increment view counter"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class DocumentVersion(models.Model):
    """Track document versions"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    version_number = models.IntegerField()
    file = models.FileField(upload_to=version_upload_path)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(help_text="Size in bytes")
    
    # Version metadata
    change_summary = models.TextField(blank=True, help_text="What changed in this version")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_versions'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['document', 'version_number']
        indexes = [
            models.Index(fields=['document', '-version_number']),
        ]
    
    def __str__(self):
        return f"{self.document.title} - Version {self.version_number}"


class DocumentAccess(models.Model):
    """Track document access history for audit purposes"""
    
    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('share', 'Shared'),
        ('update', 'Updated'),
    ]
    
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='document_accesses'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    version_number = models.IntegerField(null=True, blank=True)
    
    # Audit trail
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-accessed_at']
        verbose_name_plural = "Document Access Logs"
        indexes = [
            models.Index(fields=['document', '-accessed_at']),
            models.Index(fields=['user', '-accessed_at']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.document.title}"


class DocumentShare(models.Model):
    """Track document sharing"""
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    shared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shared_documents'
    )
    shared_with = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_documents'
    )
    
    # Share settings
    can_download = models.BooleanField(default=True)
    can_reshare = models.BooleanField(default=False)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    message = models.TextField(blank=True, help_text="Optional message with share")
    
    created_at = models.DateTimeField(auto_now_add=True)
    accessed = models.BooleanField(default=False)
    accessed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['document', 'shared_with']
    
    def __str__(self):
        return f"{self.document.title} shared with {self.shared_with}"
    
    def is_expired(self):
        """Check if share has expired"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
