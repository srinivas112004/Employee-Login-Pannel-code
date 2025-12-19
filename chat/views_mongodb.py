"""
Updated Chat Views with MongoDB Integration
This version saves data to MongoDB while maintaining the same API interface
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime
from bson import ObjectId

from .mongo_service import (
    ChatMongoService, MessageMongoService,
    OnlineStatusMongoService, NotificationMongoService
)
from authentication.models import User


class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    Chat room management with MongoDB backend
    All data is stored in MongoDB instead of Django ORM
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        """List all chat rooms for current user"""
        user_id = request.user.id
        
        # Get rooms from MongoDB
        rooms = ChatMongoService.get_user_chat_rooms(user_id)
        
        # Filter by room type if provided
        room_type = request.query_params.get('room_type')
        if room_type:
            rooms = [room for room in rooms if room['room_type'] == room_type]
        
        # Enrich with user details
        for room in rooms:
            room['id'] = room['_id']
            room['participants_details'] = self._get_user_details(room['participants'])
            room['created_by_details'] = self._get_user_details([room['created_by']])[0] if room.get('created_by') else None
        
        return Response(rooms)
    
    def create(self, request, *args, **kwargs):
        """Create new chat room in MongoDB"""
        data = request.data
        
        # Validate required fields
        if not data.get('name'):
            return Response({'error': 'Room name is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not data.get('room_type'):
            return Response({'error': 'Room type is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not data.get('participants') or len(data.get('participants', [])) < 2:
            return Response({'error': 'At least 2 participants are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate room type
        valid_room_types = ['direct', 'group', 'department', 'broadcast']
        if data['room_type'] not in valid_room_types:
            return Response({'error': f'Invalid room type. Must be one of: {valid_room_types}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For direct chats, ensure exactly 2 participants
        if data['room_type'] == 'direct' and len(data['participants']) != 2:
            return Response({'error': 'Direct chat must have exactly 2 participants'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if users exist
        participant_ids = data['participants']
        users = User.objects.filter(id__in=participant_ids)
        if users.count() != len(participant_ids):
            return Response({'error': 'One or more participants not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate identifier
        identifier = data.get('identifier')
        if not identifier:
            if data['room_type'] == 'direct':
                sorted_ids = sorted(participant_ids)
                identifier = f"direct_{sorted_ids[0]}_{sorted_ids[1]}"
            else:
                import uuid
                identifier = f"{data['room_type']}_{uuid.uuid4().hex[:8]}"
        
        # Create room in MongoDB
        room_data = {
            'name': data['name'],
            'room_type': data['room_type'],
            'participants': participant_ids,
            'created_by': request.user.id,
            'identifier': identifier
        }
        
        room = ChatMongoService.create_chat_room(room_data)
        
        # Enrich response with user details
        room['id'] = room['_id']
        room['participants_details'] = self._get_user_details(room['participants'])
        room['created_by_details'] = self._get_user_details([room['created_by']])[0]
        
        return Response(room, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """Get single chat room by ID"""
        try:
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is participant
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            # Enrich with user details
            room['id'] = room['_id']
            room['participants_details'] = self._get_user_details(room['participants'])
            room['created_by_details'] = self._get_user_details([room['created_by']])[0] if room.get('created_by') else None
            
            return Response(room)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """Get messages for a chat room"""
        try:
            # Verify room exists and user is participant
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            # Pagination parameters
            limit = int(request.query_params.get('limit', 50))
            skip = int(request.query_params.get('skip', 0))
            
            # Get messages from MongoDB
            messages = MessageMongoService.get_room_messages(pk, limit=limit, skip=skip)
            
            # Enrich with sender details
            for msg in messages:
                msg['id'] = msg['_id']
                sender = User.objects.filter(id=msg['sender_id']).first()
                if sender:
                    msg['sender'] = {
                        'id': sender.id,
                        'email': sender.email,
                        'first_name': sender.first_name,
                        'last_name': sender.last_name
                    }
            
            # Mark messages as read
            for msg in messages:
                if request.user.id not in msg.get('read_by', []) and msg['sender_id'] != request.user.id:
                    MessageMongoService.mark_as_read(msg['_id'], request.user.id)
            
            return Response({
                'count': len(messages),
                'results': messages
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='add-participant')
    def add_participant(self, request, pk=None):
        """Add participant to chat room"""
        try:
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only room creator or admin can add participants
            if request.user.id != room['created_by'] and not request.user.is_staff:
                return Response({'error': 'Only room creator or admin can add participants'}, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Add participant
            success = ChatMongoService.add_participant(pk, user_id)
            
            if success:
                return Response({'message': 'Participant added successfully'})
            else:
                return Response({'error': 'Failed to add participant'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='remove-participant')
    def remove_participant(self, request, pk=None):
        """Remove participant from chat room"""
        try:
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only room creator or admin can remove participants
            if request.user.id != room['created_by'] and not request.user.is_staff:
                return Response({'error': 'Only room creator or admin can remove participants'}, status=status.HTTP_403_FORBIDDEN)
            
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove participant
            success = ChatMongoService.remove_participant(pk, user_id)
            
            if success:
                return Response({'message': 'Participant removed successfully'})
            else:
                return Response({'error': 'Failed to remove participant'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_user_details(self, user_ids):
        """Helper to get user details"""
        users = User.objects.filter(id__in=user_ids)
        return [
            {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
            for user in users
        ]


class MessageViewSet(viewsets.ViewSet):
    """
    Message management with MongoDB backend
    """
    permission_classes = [IsAuthenticated]
    
    def create(self, request):
        """Send a new message"""
        data = request.data
        
        # Validate required fields
        if not data.get('room'):
            return Response({'error': 'room is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not data.get('content'):
            return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        room_id = data['room']
        
        try:
            # Verify room exists and user is participant
            room = ChatMongoService.get_chat_room(room_id)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            # Create message in MongoDB
            message_data = {
                'room_id': room_id,
                'sender_id': request.user.id,
                'content': data['content'],
                'message_type': data.get('message_type', 'text'),
                'parent_message_id': data.get('parent_message')
            }
            
            message = MessageMongoService.create_message(message_data)
            
            # Enrich with sender details
            message['id'] = message['_id']
            message['sender'] = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name
            }
            message['room'] = room_id
            
            # Create notifications for other participants
            for participant_id in room['participants']:
                if participant_id != request.user.id:
                    NotificationMongoService.create_notification({
                        'user_id': participant_id,
                        'room_id': room_id,
                        'message_id': message['_id'],
                        'notification_type': 'new_message'
                    })
            
            return Response(message, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        """Edit a message"""
        try:
            message = MessageMongoService.get_message(pk)
            if not message:
                return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only sender can edit
            if message['sender_id'] != request.user.id:
                return Response({'error': 'You can only edit your own messages'}, status=status.HTTP_403_FORBIDDEN)
            
            new_content = request.data.get('content')
            if not new_content:
                return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            success = MessageMongoService.update_message(pk, new_content)
            
            if success:
                updated_message = MessageMongoService.get_message(pk)
                updated_message['id'] = updated_message['_id']
                return Response(updated_message)
            else:
                return Response({'error': 'Failed to update message'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete a message (soft delete)"""
        try:
            message = MessageMongoService.get_message(pk)
            if not message:
                return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only sender can delete
            if message['sender_id'] != request.user.id:
                return Response({'error': 'You can only delete your own messages'}, status=status.HTTP_403_FORBIDDEN)
            
            success = MessageMongoService.delete_message(pk)
            
            if success:
                return Response({'message': 'Message deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete message'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        try:
            message = MessageMongoService.get_message(pk)
            if not message:
                return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
            success = MessageMongoService.mark_as_read(pk, request.user.id)
            
            if success:
                return Response({'message': 'Message marked as read'})
            else:
                return Response({'error': 'Failed to mark message as read'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserOnlineStatusViewSet(viewsets.ViewSet):
    """User online status with MongoDB backend"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='set-online')
    def set_online(self, request):
        """Set user online status"""
        is_online = request.data.get('is_online', True)
        
        try:
            OnlineStatusMongoService.set_user_status(request.user.id, is_online)
            return Response({'message': 'Status updated successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='online-users')
    def online_users(self, request):
        """Get list of online users"""
        try:
            # Get user IDs from query params or use all users
            user_ids_param = request.query_params.get('user_ids')
            if user_ids_param:
                user_ids = [int(id) for id in user_ids_param.split(',')]
            else:
                user_ids = list(User.objects.values_list('id', flat=True))
            
            statuses = OnlineStatusMongoService.get_online_users(user_ids)
            
            # Enrich with user details
            for status in statuses:
                user = User.objects.filter(id=status['user_id']).first()
                if user:
                    status['user'] = {
                        'id': user.id,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
            
            return Response(statuses)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChatNotificationViewSet(viewsets.ViewSet):
    """Chat notifications with MongoDB backend"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get all notifications for current user"""
        try:
            notifications = NotificationMongoService.get_user_notifications(request.user.id)
            
            for notif in notifications:
                notif['id'] = notif['_id']
            
            return Response(notifications)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """Get unread notifications"""
        try:
            notifications = NotificationMongoService.get_user_notifications(request.user.id, unread_only=True)
            
            for notif in notifications:
                notif['id'] = notif['_id']
            
            return Response(notifications)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        try:
            success = NotificationMongoService.mark_as_read(pk)
            
            if success:
                return Response({'message': 'Notification marked as read'})
            else:
                return Response({'error': 'Failed to mark notification as read'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        try:
            count = NotificationMongoService.mark_all_as_read(request.user.id)
            return Response({'message': f'{count} notifications marked as read'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread notifications"""
        try:
            count = NotificationMongoService.get_unread_count(request.user.id)
            return Response({'count': count})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
