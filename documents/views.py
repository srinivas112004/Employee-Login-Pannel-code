"""
Views for Document Management System
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db.models import Q

from .models import (
    DocumentCategory, Document, DocumentVersion,
    DocumentAccess, DocumentShare
)
from .serializers import (
    DocumentCategorySerializer, DocumentListSerializer,
    DocumentDetailSerializer, DocumentCreateUpdateSerializer,
    DocumentVersionSerializer, DocumentAccessSerializer,
    DocumentShareSerializer
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


class DocumentCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document Categories
    
    Permissions:
    - list, retrieve: All authenticated users
    - create, update, delete: Admin/HR only
    """
    queryset = DocumentCategory.objects.all()
    serializer_class = DocumentCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdminOrHR()]
        return [IsAuthenticated()]


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Documents
    
    Permissions:
    - list, retrieve: Authenticated users (filtered by access)
    - create: All authenticated users
    - update, delete: Owner, Admin, or HR
    - download, share: Users with access
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Support file upload and JSON
    
    def get_queryset(self):
        """Filter documents based on user access"""
        user = self.request.user
        queryset = Document.objects.select_related(
            'category', 'uploaded_by'
        ).prefetch_related('allowed_users')
        
        # Admin/HR can see all documents
        if user.role in ['admin', 'hr']:
            return queryset.all()
        
        # Filter by access level
        q_filters = Q(uploaded_by=user)  # Own documents
        q_filters |= Q(access_level='company')  # Company-wide documents
        q_filters |= Q(access_level='department', department=user.department)  # Department documents
        q_filters |= Q(allowed_users=user)  # Explicitly shared
        
        # Documents with role-based access
        if user.role:
            # SQLite compatible - filter in Python later if needed
            all_docs = list(queryset.filter(q_filters).distinct())
            role_docs = [doc for doc in all_docs if not doc.allowed_roles or user.role in doc.allowed_roles]
            doc_ids = [doc.id for doc in role_docs]
            return queryset.filter(id__in=doc_ids) if doc_ids else queryset.filter(q_filters).distinct()
        
        return queryset.filter(q_filters).distinct()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DocumentCreateUpdateSerializer
        return DocumentDetailSerializer
    
    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Create document and log the action"""
        document = serializer.save()
        
        # Log document creation
        DocumentAccess.objects.create(
            document=document,
            user=self.request.user,
            action='update',
            version_number=1,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def perform_update(self, serializer):
        """Update document and log the action"""
        document = serializer.save()
        
        # Log document update
        DocumentAccess.objects.create(
            document=document,
            user=self.request.user,
            action='update',
            version_number=document.current_version,
            ip_address=get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def destroy(self, request, *args, **kwargs):
        """Check permissions before deleting"""
        document = self.get_object()
        user = request.user
        
        # Only owner, admin, or HR can delete
        if document.uploaded_by != user and user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'You do not have permission to delete this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file"""
        document = self.get_object()
        
        # Check access
        if not self._check_user_access(document, request.user):
            return Response(
                {'error': 'You do not have permission to access this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Increment download count
        document.increment_download_count()
        
        # Log download
        DocumentAccess.objects.create(
            document=document,
            user=request.user,
            action='download',
            version_number=document.current_version,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return file
        try:
            response = FileResponse(
                document.file.open('rb'),
                as_attachment=True,
                filename=document.file_name
            )
            # Add CORS headers for file download
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """List all versions of a document"""
        document = self.get_object()
        
        # Check access
        if not self._check_user_access(document, request.user):
            return Response(
                {'error': 'You do not have permission to access this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        versions = document.versions.all()
        serializer = DocumentVersionSerializer(versions, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='versions/(?P<version_number>[0-9]+)/download')
    def download_version(self, request, pk=None, version_number=None):
        """Download a specific version of a document"""
        document = self.get_object()
        
        # Check access
        if not self._check_user_access(document, request.user):
            return Response(
                {'error': 'You do not have permission to access this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            version = DocumentVersion.objects.get(
                document=document,
                version_number=version_number
            )
        except DocumentVersion.DoesNotExist:
            raise Http404("Version not found")
        
        # Log download
        DocumentAccess.objects.create(
            document=document,
            user=request.user,
            action='download',
            version_number=int(version_number),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return file
        try:
            response = FileResponse(
                version.file.open('rb'),
                as_attachment=True,
                filename=version.file_name
            )
            # Add CORS headers for file download
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share document with another user"""
        document = self.get_object()
        
        # Check if user can share
        if not self._check_user_access(document, request.user):
            return Response(
                {'error': 'You do not have permission to share this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = DocumentShareSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(document=document)
            
            # Log share action
            DocumentAccess.objects.create(
                document=document,
                user=request.user,
                action='share',
                version_number=document.current_version,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a document"""
        document = self.get_object()
        user = request.user
        
        # Only owner, admin, or HR can archive
        if document.uploaded_by != user and user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'You do not have permission to archive this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.status = 'archived'
        document.archived_at = timezone.now()
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore an archived document"""
        document = self.get_object()
        user = request.user
        
        # Only owner, admin, or HR can restore
        if document.uploaded_by != user and user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'You do not have permission to restore this document'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        document.status = 'active'
        document.archived_at = None
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def access_logs(self, request, pk=None):
        """Get access logs for a document (Owner/Admin/HR only)"""
        document = self.get_object()
        user = request.user
        
        # Only owner, admin, or HR can view access logs
        if document.uploaded_by != user and user.role not in ['admin', 'hr']:
            return Response(
                {'error': 'You do not have permission to view access logs'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        logs = document.access_logs.all()
        serializer = DocumentAccessSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_documents(self, request):
        """Get documents uploaded by current user"""
        documents = Document.objects.filter(
            uploaded_by=request.user
        ).select_related('category', 'uploaded_by')
        
        serializer = DocumentListSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def shared_with_me(self, request):
        """Get documents shared with current user"""
        shares = DocumentShare.objects.filter(
            shared_with=request.user
        ).select_related('document', 'shared_by')
        
        # Filter out expired shares
        active_shares = [share for share in shares if not share.is_expired()]
        
        documents = [share.document for share in active_shares]
        serializer = DocumentListSerializer(documents, many=True, context={'request': request})
        return Response(serializer.data)
    
    def _check_user_access(self, document, user):
        """Check if user has access to document"""
        if user.role in ['admin', 'hr']:
            return True
        if document.uploaded_by == user:
            return True
        if document.access_level == 'company':
            return True
        elif document.access_level == 'department':
            return document.department == user.department
        elif document.access_level == 'team':
            if user in document.allowed_users.all():
                return True
            if document.allowed_roles and user.role in document.allowed_roles:
                return True
        elif document.access_level == 'private':
            return user in document.allowed_users.all()
        return False


class DocumentShareViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Document Shares (Read-only)
    """
    serializer_class = DocumentShareSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get shares relevant to current user"""
        user = self.request.user
        
        # Admin/HR can see all shares
        if user.role in ['admin', 'hr']:
            return DocumentShare.objects.select_related(
                'document', 'shared_by', 'shared_with'
            ).all()
        
        # Users can see shares they created or received
        return DocumentShare.objects.filter(
            Q(shared_by=user) | Q(shared_with=user)
        ).select_related('document', 'shared_by', 'shared_with')
