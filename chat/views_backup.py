from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from .models import ChatRoom, Message, UserOnlineStatus, ChatNotification
from .serializers import (
    ChatRoomSerializer, ChatRoomCreateSerializer, MessageSerializer,
    MessageCreateSerializer, UserOnlineStatusSerializer, ChatNotificationSerializer
)
from authentication.models import User


class ChatRoomViewSet(viewsets.ModelViewSet):
    """Chat room management endpoints"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get rooms where user is a participant"""
        return ChatRoom.objects.filter(
            participants=self.request.user,
            is_active=True
        ).prefetch_related('participants', 'created_by').annotate(
            message_count=Count('messages')
        )
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer
    
    def list(self, request, *args, **kwargs):
        """List all chat rooms for current user"""
        queryset = self.get_queryset().order_by('-updated_at')
        
        # Filter by room type if provided
        room_type = request.query_params.get('room_type')
        if room_type:
            queryset = queryset.filter(room_type=room_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create new chat room"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        room = serializer.save()
        
        # Return full room details
        response_serializer = ChatRoomSerializer(room, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """Get messages for a chat room"""
        room = self.get_object()
        
        # Pagination parameters
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Get messages
        messages_queryset = Message.objects.filter(
            room=room,
            deleted=False
        ).select_related('sender', 'reply_to').prefetch_related('read_by')
        
        total_count = messages_queryset.count()
        messages = messages_queryset[offset:offset + limit]
        
        serializer = MessageSerializer(messages, many=True)
        
        # Mark messages as read
        unread_messages = messages_queryset.exclude(sender=request.user).exclude(read_by=request.user)
        for msg in unread_messages:
            msg.mark_as_read(request.user)
        
        return Response({
            'count': total_count,
            'next': offset + limit < total_count,
            'previous': offset > 0,
            'results': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='send-message')
    def send_message(self, request, pk=None):
        """Send a message to chat room"""
        room = self.get_object()
        
        # Check if user is participant
        if request.user not in room.participants.all():
            return Response(
                {'error': 'You are not a participant of this room'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message = serializer.save(sender=request.user, room=room)
        
        # Update room timestamp
        room.updated_at = timezone.now()
        room.save(update_fields=['updated_at'])
        
        # Create notifications for other participants
        for participant in room.participants.exclude(id=request.user.id):
            ChatNotification.objects.create(
                user=participant,
                room=room,
                message=message
            )
        
        response_serializer = MessageSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark all messages in room as read"""
        room = self.get_object()
        
        # Mark all unread messages as read
        unread_messages = Message.objects.filter(
            room=room,
            deleted=False
        ).exclude(sender=request.user).exclude(read_by=request.user)
        
        for msg in unread_messages:
            msg.mark_as_read(request.user)
        
        # Mark notifications as read
        ChatNotification.objects.filter(
            user=request.user,
            room=room,
            is_read=False
        ).update(is_read=True)
        
        return Response({'message': f'Marked {unread_messages.count()} messages as read'})
    
    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """Add participant to chat room"""
        room = self.get_object()
        
        # Only group/project/department rooms can add participants
        if room.room_type == 'direct':
            return Response(
                {'error': 'Cannot add participants to direct messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            room.participants.add(user)
            
            # Create system message
            Message.objects.create(
                room=room,
                sender=request.user,
                message_type='system',
                content=f"{request.user.email} added {user.email} to the chat"
            )
            
            return Response({'message': f'Added {user.email} to the room'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='remove-participant')
    def remove_participant(self, request, pk=None):
        """Remove participant from chat room"""
        room = self.get_object()
        
        # Only group/project/department rooms can remove participants
        if room.room_type == 'direct':
            return Response(
                {'error': 'Cannot remove participants from direct messages'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
            room.participants.remove(user)
            
            # Create system message
            Message.objects.create(
                room=room,
                sender=request.user,
                message_type='system',
                content=f"{request.user.email} removed {user.email} from the chat"
            )
            
            return Response({'message': f'Removed {user.email} from the room'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Search chat rooms by name or participants"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(participants__email__icontains=query) |
            Q(participants__first_name__icontains=query) |
            Q(participants__last_name__icontains=query)
        ).distinct()
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """Message management endpoints"""
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        """Get messages from rooms where user is participant"""
        user_rooms = ChatRoom.objects.filter(participants=self.request.user)
        return Message.objects.filter(
            room__in=user_rooms,
            deleted=False
        ).select_related('sender', 'room', 'reply_to')
    
    def update(self, request, *args, **kwargs):
        """Update (edit) a message"""
        message = self.get_object()
        
        # Only sender can edit
        if message.sender != request.user:
            return Response(
                {'error': 'You can only edit your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update content
        message.content = request.data.get('content', message.content)
        message.edited = True
        message.edited_at = timezone.now()
        message.save()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Delete (soft delete) a message"""
        message = self.get_object()
        
        # Only sender can delete
        if message.sender != request.user:
            return Response(
                {'error': 'You can only delete your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.deleted = True
        message.content = "This message was deleted"
        message.save()
        
        return Response({'message': 'Message deleted successfully'})
    
    @action(detail=True, methods=['post'], url_path='react')
    def react(self, request, pk=None):
        """Add reaction to message (future feature)"""
        return Response({'message': 'Reactions feature coming soon'})


class UserOnlineStatusViewSet(viewsets.ReadOnlyModelViewSet):
    """User online status endpoints"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserOnlineStatusSerializer
    
    def get_queryset(self):
        """Get online status for all users"""
        return UserOnlineStatus.objects.select_related('user')
    
    @action(detail=False, methods=['post'], url_path='set-online')
    def set_online(self, request):
        """Set current user as online"""
        online_status, created = UserOnlineStatus.objects.get_or_create(user=request.user)
        online_status.set_online()
        
        serializer = self.get_serializer(online_status)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='set-offline')
    def set_offline(self, request):
        """Set current user as offline"""
        online_status, created = UserOnlineStatus.objects.get_or_create(user=request.user)
        online_status.set_offline()
        
        serializer = self.get_serializer(online_status)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='update-status')
    def update_status(self, request):
        """Update status message"""
        online_status, created = UserOnlineStatus.objects.get_or_create(user=request.user)
        
        status_message = request.data.get('status_message', '')
        online_status.status_message = status_message
        online_status.save()
        
        serializer = self.get_serializer(online_status)
        return Response(serializer.data)


class ChatNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Chat notification endpoints"""
    permission_classes = [IsAuthenticated]
    serializer_class = ChatNotificationSerializer
    
    def get_queryset(self):
        """Get notifications for current user"""
        return ChatNotification.objects.filter(user=self.request.user).select_related(
            'room', 'message', 'message__sender'
        )
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """Get unread notifications"""
        unread = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(unread, many=True)
        
        return Response({
            'count': unread.count(),
            'notifications': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        count = self.get_queryset().filter(is_read=False).update(is_read=True)
        
        return Response({'message': f'Marked {count} notifications as read'})
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark single notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

