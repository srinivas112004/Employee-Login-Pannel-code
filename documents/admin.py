"""
Admin configuration for documents app
"""

from django.contrib import admin
from .models import DocumentCategory, Document, DocumentVersion, DocumentAccess, DocumentShare


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'icon', 'created_at']
    search_fields = ['name', 'description']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'uploaded_by', 'current_version',
        'access_level', 'status', 'download_count', 'created_at'
    ]
    list_filter = ['status', 'access_level', 'category', 'created_at']
    search_fields = ['title', 'description', 'file_name']
    readonly_fields = ['download_count', 'view_count', 'created_at', 'updated_at']
    filter_horizontal = ['allowed_users']


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'version_number', 'uploaded_by', 'file_name', 'created_at']
    list_filter = ['created_at']
    search_fields = ['document__title', 'file_name', 'change_summary']
    readonly_fields = ['created_at']


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'action', 'version_number', 'accessed_at']
    list_filter = ['action', 'accessed_at']
    search_fields = ['document__title', 'user__email']
    readonly_fields = ['accessed_at']


@admin.register(DocumentShare)
class DocumentShareAdmin(admin.ModelAdmin):
    list_display = [
        'document', 'shared_by', 'shared_with', 'can_download',
        'expires_at', 'accessed', 'created_at'
    ]
    list_filter = ['can_download', 'can_reshare', 'accessed', 'created_at']
    search_fields = ['document__title', 'shared_by__email', 'shared_with__email']
    readonly_fields = ['created_at', 'accessed', 'accessed_at']
