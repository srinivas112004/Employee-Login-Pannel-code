"""
Views for Activity Logs and Audit Trail
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
from collections import Counter

from .mongodb_utils import activity_log_manager
from .serializers import (
    ActivityLogSerializer,
    AuditLogSerializer,
    ActivityLogFilterSerializer,
    ActivityLogStatsSerializer
)
from authentication.permissions import IsAdminOrHR


class ActivityLogViewSet(viewsets.ViewSet):
    """
    ViewSet for Activity Logs
    
    Permissions:
    - list, retrieve, search: Admin, HR
    - All other actions: Not allowed (logs are auto-created by middleware)
    """
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    def list(self, request):
        """
        Get all activity logs with optional filters
        
        Query Parameters:
        - user_id: Filter by user ID
        - action: Filter by action (CREATE, READ, UPDATE, DELETE)
        - method: Filter by HTTP method
        - model_name: Filter by model name
        - status_code: Filter by status code
        - start_date: Filter by start date (ISO format)
        - end_date: Filter by end date (ISO format)
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 200)
        """
        # Validate filters
        filter_serializer = ActivityLogFilterSerializer(data=request.query_params)
        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        filters_data = filter_serializer.validated_data
        
        # Build MongoDB filter query
        filters = {}
        
        if filters_data.get('user_id'):
            filters['user_id'] = filters_data['user_id']
        
        if filters_data.get('action'):
            filters['action'] = filters_data['action']
        
        if filters_data.get('method'):
            filters['method'] = filters_data['method']
        
        if filters_data.get('model_name'):
            filters['model_name'] = filters_data['model_name']
        
        if filters_data.get('object_id'):
            filters['object_id'] = filters_data['object_id']
        
        if filters_data.get('status_code'):
            filters['status_code'] = filters_data['status_code']
        
        # Date range filter
        if filters_data.get('start_date') or filters_data.get('end_date'):
            filters['timestamp'] = {}
            if filters_data.get('start_date'):
                filters['timestamp']['$gte'] = filters_data['start_date']
            if filters_data.get('end_date'):
                filters['timestamp']['$lte'] = filters_data['end_date']
        
        # Pagination
        page = filters_data.get('page', 1)
        page_size = filters_data.get('page_size', 50)
        skip = (page - 1) * page_size
        
        # Get logs
        logs = activity_log_manager.get_logs(filters=filters, skip=skip, limit=page_size)
        total_count = activity_log_manager.count_logs(filters=filters)
        
        # Serialize
        serializer = ActivityLogSerializer(logs, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search activity logs by text query
        
        Query Parameters:
        - q: Search query
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50)
        """
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Search query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        skip = (page - 1) * page_size
        
        # Search logs
        logs = activity_log_manager.search_logs(query=query, skip=skip, limit=page_size)
        
        # Get count (approximate)
        total_count = len(logs)  # Simple approach, could be improved with separate count query
        
        # Serialize
        serializer = ActivityLogSerializer(logs, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'query': query,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get activity log statistics
        
        Query Parameters:
        - days: Number of days to include (default: 7)
        """
        days = int(request.query_params.get('days', 7))
        
        # Date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        filters = {
            'timestamp': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        
        # Get all logs for the period
        logs = activity_log_manager.get_logs(filters=filters, limit=10000)
        
        # Calculate statistics
        total_logs = len(logs)
        unique_users = set(log.get('user_id') for log in logs if log.get('user_id'))
        
        actions = [log.get('action') for log in logs if log.get('action')]
        actions_breakdown = dict(Counter(actions))
        
        status_codes = [log.get('status_code') for log in logs if log.get('status_code')]
        status_codes_breakdown = dict(Counter(status_codes))
        
        endpoints = [log.get('endpoint') for log in logs if log.get('endpoint')]
        top_endpoints = [{'endpoint': ep, 'count': count} for ep, count in Counter(endpoints).most_common(10)]
        
        users = [(log.get('user_id'), log.get('user_name')) for log in logs if log.get('user_id')]
        user_counts = Counter(user_id for user_id, _ in users)
        user_names = {user_id: name for user_id, name in users}
        top_users = [
            {'user_id': user_id, 'user_name': user_names.get(user_id, 'Unknown'), 'count': count}
            for user_id, count in user_counts.most_common(10)
        ]
        
        # Recent errors
        error_logs = [log for log in logs if log.get('status_code', 0) >= 400]
        recent_errors = [
            {
                'timestamp': log.get('timestamp'),
                'user_name': log.get('user_name'),
                'endpoint': log.get('endpoint'),
                'status_code': log.get('status_code'),
                'error_message': log.get('error_message')
            }
            for log in error_logs[:10]
        ]
        
        # Average response time
        response_times = [log.get('response_time') for log in logs if log.get('response_time')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        stats = {
            'total_logs': total_logs,
            'total_users': len(unique_users),
            'actions_breakdown': actions_breakdown,
            'status_codes_breakdown': status_codes_breakdown,
            'top_endpoints': top_endpoints,
            'top_users': top_users,
            'recent_errors': recent_errors,
            'average_response_time': round(avg_response_time, 2)
        }
        
        serializer = ActivityLogStatsSerializer(stats)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ViewSet):
    """
    ViewSet for Audit Trail (CRUD operations only)
    
    Permissions:
    - All actions: Admin, HR only
    """
    permission_classes = [IsAuthenticated, IsAdminOrHR]
    
    def list(self, request):
        """
        Get audit trail (CRUD operations only)
        
        Query Parameters:
        - user_id: Filter by user ID
        - model_name: Filter by model name
        - object_id: Filter by object ID
        - action: Filter by action (CREATE, UPDATE, DELETE)
        - start_date: Filter by start date
        - end_date: Filter by end date
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50)
        """
        # Build filters
        filters = {
            'action': {'$in': ['CREATE', 'UPDATE', 'DELETE']}  # Exclude READ
        }
        
        if request.query_params.get('user_id'):
            filters['user_id'] = int(request.query_params.get('user_id'))
        
        if request.query_params.get('model_name'):
            filters['model_name'] = request.query_params.get('model_name')
        
        if request.query_params.get('object_id'):
            filters['object_id'] = request.query_params.get('object_id')
        
        if request.query_params.get('action'):
            action = request.query_params.get('action')
            if action in ['CREATE', 'UPDATE', 'DELETE']:
                filters['action'] = action
        
        # Date range
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date or end_date:
            filters['timestamp'] = {}
            if start_date:
                filters['timestamp']['$gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                filters['timestamp']['$lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 50))
        skip = (page - 1) * page_size
        
        # Get audit logs
        logs = activity_log_manager.get_logs(filters=filters, skip=skip, limit=page_size)
        total_count = activity_log_manager.count_logs(filters=filters)
        
        # Filter to only include relevant fields for audit
        audit_logs = []
        for log in logs:
            if log.get('model_name') and log.get('user_id'):
                audit_logs.append({
                    'id': log.get('id'),
                    'timestamp': log.get('timestamp'),
                    'user_id': log.get('user_id'),
                    'user_name': log.get('user_name'),
                    'action': log.get('action'),
                    'model_name': log.get('model_name'),
                    'object_id': log.get('object_id'),
                    'changes': log.get('changes'),
                    'endpoint': log.get('endpoint'),
                    'ip_address': log.get('ip_address')
                })
        
        # Serialize
        serializer = AuditLogSerializer(audit_logs, many=True)
        
        return Response({
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='object/(?P<model_name>[^/.]+)/(?P<object_id>[^/.]+)')
    def object_history(self, request, model_name=None, object_id=None):
        """
        Get complete audit history for a specific object
        
        URL: /api/logs/audit/object/{model_name}/{object_id}/
        """
        logs = activity_log_manager.get_audit_trail(
            model_name=model_name,
            object_id=object_id,
            limit=100
        )
        
        # Filter and format
        audit_logs = []
        for log in logs:
            if log.get('user_id'):
                audit_logs.append({
                    'id': log.get('id'),
                    'timestamp': log.get('timestamp'),
                    'user_id': log.get('user_id'),
                    'user_name': log.get('user_name'),
                    'action': log.get('action'),
                    'model_name': log.get('model_name'),
                    'object_id': log.get('object_id'),
                    'changes': log.get('changes'),
                    'endpoint': log.get('endpoint'),
                    'ip_address': log.get('ip_address')
                })
        
        serializer = AuditLogSerializer(audit_logs, many=True)
        
        return Response({
            'model_name': model_name,
            'object_id': object_id,
            'count': len(audit_logs),
            'results': serializer.data
        })
