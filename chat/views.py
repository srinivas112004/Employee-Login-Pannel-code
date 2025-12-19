"""
Updated Chat Views with MongoDB Integration
This version saves data to MongoDB while maintaining the same API interface
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.core.files.storage import default_storage
from datetime import datetime
from bson import ObjectId
import os
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .mongo_service import (
    ChatMongoService, MessageMongoService,
    OnlineStatusMongoService, NotificationMongoService,
    ChannelMongoService
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
        
        # Handle both participant_emails and participants
        participant_ids = []
        
        if data.get('participant_emails'):
            # Convert emails to user IDs
            emails = data['participant_emails']
            if len(emails) < 2:
                return Response({'error': 'At least 2 participants are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            users = User.objects.filter(email__in=emails)
            if users.count() != len(emails):
                found_emails = list(users.values_list('email', flat=True))
                missing = set(emails) - set(found_emails)
                return Response({
                    'error': f'Users not found with emails: {list(missing)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            participant_ids = [user.id for user in users]
        
        elif data.get('participants'):
            participant_ids = data['participants']
            if len(participant_ids) < 2:
                return Response({'error': 'At least 2 participants are required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if users exist
            users = User.objects.filter(id__in=participant_ids)
            if users.count() != len(participant_ids):
                return Response({'error': 'One or more participants not found'}, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({
                'error': 'Either participants (user IDs) or participant_emails must be provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate room type
        valid_room_types = ['direct', 'group', 'department', 'broadcast']
        if data['room_type'] not in valid_room_types:
            return Response({'error': f'Invalid room type. Must be one of: {valid_room_types}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # For direct chats, ensure exactly 2 participants
        if data['room_type'] == 'direct' and len(participant_ids) != 2:
            return Response({'error': 'Direct chat must have exactly 2 participants'}, status=status.HTTP_400_BAD_REQUEST)
        
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
    
    def partial_update(self, request, pk=None):
        """Update chat room (e.g., participants list)"""
        try:
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only room creator or admin can update
            if request.user.id != room['created_by'] and not request.user.is_staff:
                return Response(
                    {'error': 'Only room creator or admin can update this room'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Handle participants update - accept multiple field names
            participants = None
            if 'participants' in request.data:
                participants = request.data['participants']
            elif 'participants_ids' in request.data:
                participants = request.data['participants_ids']
            elif 'participant_ids' in request.data:
                participants = request.data['participant_ids']
            
            if participants is not None:
                # Validate participants
                if not isinstance(participants, list):
                    return Response({'error': 'participants must be a list'}, status=status.HTTP_400_BAD_REQUEST)
                
                if len(participants) < 2:
                    return Response({'error': 'At least 2 participants are required'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if users exist
                users = User.objects.filter(id__in=participants)
                if users.count() != len(participants):
                    return Response({'error': 'One or more participants not found'}, status=status.HTTP_400_BAD_REQUEST)
                
                # Update participants in MongoDB
                success = ChatMongoService.update_room_participants(pk, participants)
                
                if not success:
                    return Response({'error': 'Failed to update participants'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Get updated room
            updated_room = ChatMongoService.get_chat_room(pk)
            updated_room['id'] = updated_room['_id']
            updated_room['participants_details'] = self._get_user_details(updated_room['participants'])
            updated_room['created_by_details'] = self._get_user_details([updated_room['created_by']])[0] if updated_room.get('created_by') else None
            
            return Response(updated_room)
        except Exception as e:
            import traceback
            print(f"Error in partial_update: {str(e)}")
            print(traceback.format_exc())
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
    
    def destroy(self, request, pk=None):
        """Delete a chat room"""
        try:
            room = ChatMongoService.get_chat_room(pk)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Only room creator or admin can delete
            if request.user.id != room['created_by'] and not request.user.is_staff:
                return Response(
                    {'error': 'Only room creator or admin can delete this room'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Soft delete the room
            success = ChatMongoService.delete_chat_room(pk)
            
            if success:
                return Response({'message': 'Room deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete room'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """Search chat rooms by name"""
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Search query (q) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get all user's rooms
            user_id = request.user.id
            rooms = ChatMongoService.get_user_chat_rooms(user_id)
            
            # Filter by search query (case-insensitive)
            filtered_rooms = [
                room for room in rooms
                if query.lower() in room['name'].lower()
            ]
            
            # Enrich with user details
            for room in filtered_rooms:
                room['id'] = room['_id']
                room['participants_details'] = self._get_user_details(room['participants'])
                room['created_by_details'] = self._get_user_details([room['created_by']])[0] if room.get('created_by') else None
            
            return Response(filtered_rooms)
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
            
            # Check if user has access to this message (must be in the room)
            room = ChatMongoService.get_chat_room(message['room_id'])
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            success = MessageMongoService.mark_as_read(pk, request.user.id)
            
            if success:
                return Response({'message': 'Message marked as read', 'status': 'success'})
            else:
                return Response({'error': 'Failed to mark message as read'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            print(f"Error in mark_read: {str(e)}")
            print(traceback.format_exc())
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='react')
    def add_reaction(self, request, pk=None):
        """
        Add reaction (emoji) to a message
        
        Body: {"emoji": "👍"}
        """
        try:
            message = MessageMongoService.get_message(pk)
            if not message:
                return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
            emoji = request.data.get('emoji')
            if not emoji:
                return Response({'error': 'emoji is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            success = MessageMongoService.add_reaction(pk, request.user.id, emoji)
            
            if success:
                updated_message = MessageMongoService.get_message(pk)
                updated_message['id'] = updated_message['_id']
                return Response({
                    'message': 'Reaction added successfully',
                    'reactions': updated_message.get('reactions', {})
                })
            else:
                return Response({'error': 'Failed to add reaction'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], url_path='react')
    def remove_reaction(self, request, pk=None):
        """
        Remove reaction from a message
        
        Query params: ?emoji=👍
        """
        try:
            message = MessageMongoService.get_message(pk)
            if not message:
                return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
            emoji = request.query_params.get('emoji')
            if not emoji:
                return Response({'error': 'emoji query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            success = MessageMongoService.remove_reaction(pk, request.user.id, emoji)
            
            if success:
                updated_message = MessageMongoService.get_message(pk)
                updated_message['id'] = updated_message['_id']
                return Response({
                    'message': 'Reaction removed successfully',
                    'reactions': updated_message.get('reactions', {})
                })
            else:
                return Response({'error': 'Failed to remove reaction'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search messages in a room
        
        Query params: ?room=<room_id>&q=<search_query>
        """
        room_id = request.query_params.get('room')
        query = request.query_params.get('q', '')
        
        if not room_id:
            return Response({'error': 'room query parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not query:
            return Response({'error': 'q (search query) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Verify room exists and user is participant
            room = ChatMongoService.get_chat_room(room_id)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            # Search messages
            messages = MessageMongoService.search_messages(room_id, query)
            
            # Enrich with sender details
            for message in messages:
                message['id'] = message['_id']
                # Note: In production, you'd batch-fetch user details
                sender = User.objects.filter(id=message['sender_id']).first()
                if sender:
                    message['sender'] = {
                        'id': sender.id,
                        'email': sender.email,
                        'first_name': sender.first_name,
                        'last_name': sender.last_name
                    }
            
            return Response({
                'count': len(messages),
                'results': messages
            })
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
            # Validate ObjectId format
            from bson import ObjectId
            if not ObjectId.is_valid(pk):
                return Response({
                    'error': 'Invalid notification ID format',
                    'detail': f'The ID "{pk}" is not a valid MongoDB ObjectId (must be 24 hex characters)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            success = NotificationMongoService.mark_as_read(pk)
            
            if success:
                return Response({
                    'message': 'Notification marked as read',
                    'notification_id': pk
                })
            else:
                return Response({
                    'error': 'Notification not found',
                    'detail': f'No notification exists with ID "{pk}"'
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to mark notification as read',
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
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


class FileUploadViewSet(viewsets.ViewSet):
    """Handle file uploads in chat rooms"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_file(self, request):
        """
        Upload file to chat room
        
        Request:
            - file: File object (required)
            - room_id: Room ID (required)
            - content: Optional caption/message
        """
        try:
            file = request.FILES.get('file')
            room_id = request.data.get('room_id')
            content = request.data.get('content', '')
            
            if not file:
                return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not room_id:
                return Response({'error': 'Room ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify room exists and user is participant
            room = ChatMongoService.get_chat_room(room_id)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            # Save file
            file_name = file.name
            file_path = f'chat_files/{room_id}/{file_name}'
            saved_path = default_storage.save(file_path, file)
            file_url = default_storage.url(saved_path)
            
            # Determine file type
            file_extension = os.path.splitext(file_name)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                file_type = 'image'
            elif file_extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                file_type = 'video'
            elif file_extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
                file_type = 'document'
            elif file_extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                file_type = 'archive'
            else:
                file_type = 'other'
            
            # Create file message in MongoDB
            message_data = {
                'room_id': room_id,
                'sender_id': request.user.id,
                'content': content,
                'file_url': file_url,
                'file_name': file_name,
                'file_type': file_type,
                'file_size': file.size
            }
            
            message = MessageMongoService.create_file_message(message_data)
            
            # Enrich with sender details
            sender = User.objects.get(id=request.user.id)
            message['sender'] = {
                'id': sender.id,
                'email': sender.email,
                'first_name': sender.first_name,
                'last_name': sender.last_name
            }
            
            return Response({
                'message': 'File uploaded successfully',
                'data': message
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='room-files')
    def get_room_files(self, request):
        """
        Get all files shared in a room
        
        Query params:
            - room_id: Room ID (required)
            - file_type: Filter by type (optional)
            - limit: Results per page (default: 50)
            - offset: Pagination offset (default: 0)
        """
        try:
            room_id = request.query_params.get('room_id')
            file_type = request.query_params.get('file_type')
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            if not room_id:
                return Response({'error': 'Room ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify room exists and user is participant
            room = ChatMongoService.get_chat_room(room_id)
            if not room:
                return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if request.user.id not in room['participants']:
                return Response({'error': 'You are not a participant of this room'}, status=status.HTTP_403_FORBIDDEN)
            
            result = MessageMongoService.get_room_files(room_id, file_type, limit, offset)
            
            # Enrich with sender details
            for file_msg in result['files']:
                try:
                    sender = User.objects.get(id=file_msg['sender_id'])
                    file_msg['sender'] = {
                        'id': sender.id,
                        'email': sender.email,
                        'first_name': sender.first_name,
                        'last_name': sender.last_name
                    }
                except User.DoesNotExist:
                    file_msg['sender'] = None
            
            return Response(result)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ChannelViewSet(viewsets.ViewSet):
    """Department/Project channels management"""
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List all channels for current user"""
        try:
            channel_type = request.query_params.get('type')
            
            if channel_type:
                channels = ChannelMongoService.get_channels_by_type(channel_type)
            else:
                channels = ChannelMongoService.get_user_channels(request.user.id)
            
            # Enrich with user details
            for channel in channels:
                channel['id'] = channel['_id']
                channel['created_by_details'] = self._get_user_details([channel['created_by']])[0] if channel.get('created_by') else None
                channel['admin_details'] = self._get_user_details(channel.get('admins', []))
                channel['member_count'] = len(channel.get('members', []))
            
            return Response(channels)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request):
        """Create new channel"""
        try:
            data = request.data
            
            # Validate required fields
            if not data.get('name'):
                return Response({'error': 'Channel name is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Set creator
            data['created_by'] = request.user.id
            
            # Handle member_emails if provided
            if 'member_emails' in data:
                member_emails = data.pop('member_emails')
                users = User.objects.filter(email__in=member_emails)
                data['members'] = [user.id for user in users]
                
                # Check if all emails were found
                found_emails = [user.email for user in users]
                not_found = [email for email in member_emails if email not in found_emails]
                if not_found:
                    return Response({
                        'error': f'Users not found with emails: {not_found}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create channel
            channel = ChannelMongoService.create_channel(data)
            
            # Enrich with user details
            channel['id'] = channel['_id']
            creator = User.objects.get(id=request.user.id)
            channel['created_by_details'] = {
                'id': creator.id,
                'email': creator.email,
                'first_name': creator.first_name,
                'last_name': creator.last_name
            }
            
            return Response(channel, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """Get channel details"""
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user has access
            user_id = request.user.id
            if not channel.get('is_public') and user_id not in channel.get('members', []) and user_id not in channel.get('admins', []):
                return Response({'error': 'You do not have access to this channel'}, status=status.HTTP_403_FORBIDDEN)
            
            # Enrich with user details
            channel['id'] = channel['_id']
            channel['created_by_details'] = self._get_user_details([channel['created_by']])[0] if channel.get('created_by') else None
            channel['admin_details'] = self._get_user_details(channel.get('admins', []))
            channel['member_details'] = self._get_user_details(channel.get('members', []))
            
            return Response(channel)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update channel (admins only)"""
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is admin
            if request.user.id not in channel.get('admins', []):
                return Response({'error': 'Only admins can update channel'}, status=status.HTTP_403_FORBIDDEN)
            
            # Update channel
            update_data = {k: v for k, v in request.data.items() if k in ['name', 'description', 'settings']}
            success = ChannelMongoService.update_channel(pk, update_data)
            
            if success:
                return Response({'message': 'Channel updated successfully'})
            else:
                return Response({'error': 'Failed to update channel'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """Delete channel (admins only)"""
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user is admin or creator
            if request.user.id not in channel.get('admins', []) and request.user.id != channel.get('created_by'):
                return Response({'error': 'Only admins can delete channel'}, status=status.HTTP_403_FORBIDDEN)
            
            success = ChannelMongoService.delete_channel(pk)
            
            if success:
                return Response({'message': 'Channel deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'error': 'Failed to delete channel'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='broadcast')
    def broadcast_message(self, request, pk=None):
        """
        Broadcast message to channel
        
        Request:
            - content: Message content (required)
            - message_type: Type (default: 'text')
        """
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check if user can post
            user_id = request.user.id
            is_admin = user_id in channel.get('admins', [])
            is_member = user_id in channel.get('members', [])
            allow_member_posts = channel.get('settings', {}).get('allow_member_posts', True)
            
            if not is_admin and not (is_member and allow_member_posts):
                return Response({'error': 'You do not have permission to post in this channel'}, status=status.HTTP_403_FORBIDDEN)
            
            content = request.data.get('content')
            if not content:
                return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create broadcast message
            message_data = {
                'channel_id': pk,
                'sender_id': user_id,
                'content': content,
                'message_type': request.data.get('message_type', 'text')
            }
            
            message = ChannelMongoService.broadcast_message(message_data)
            
            # Enrich with sender details
            sender = User.objects.get(id=user_id)
            message['sender'] = {
                'id': sender.id,
                'email': sender.email,
                'first_name': sender.first_name,
                'last_name': sender.last_name
            }
            
            # Prepare data for WebSocket (convert datetime to string)
            ws_message_data = {
                '_id': str(message.get('_id', '')),
                'channel_id': str(message.get('channel_id', pk)),
                'content': message.get('content'),
                'message_type': message.get('message_type'),
                'sender_id': user_id,
                'created_at': message.get('created_at').isoformat() if hasattr(message.get('created_at'), 'isoformat') else str(message.get('created_at', ''))
            }
            
            # Send real-time notification via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'channel_{pk}',
                {
                    'type': 'broadcast_message',
                    'data': ws_message_data,
                    'sender_id': user_id,
                    'sender_name': sender.get_full_name(),
                    'timestamp': ws_message_data['created_at']
                }
            )
            
            return Response({
                'message': 'Broadcast sent successfully',
                'data': message
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        """Get messages from channel"""
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Check access
            user_id = request.user.id
            if not channel.get('is_public') and user_id not in channel.get('members', []) and user_id not in channel.get('admins', []):
                return Response({'error': 'You do not have access to this channel'}, status=status.HTTP_403_FORBIDDEN)
            
            limit = int(request.query_params.get('limit', 50))
            offset = int(request.query_params.get('offset', 0))
            
            result = ChannelMongoService.get_channel_messages(pk, limit, offset)
            
            # Enrich with sender details
            for msg in result['messages']:
                try:
                    sender = User.objects.get(id=msg['sender_id'])
                    msg['sender'] = {
                        'id': sender.id,
                        'email': sender.email,
                        'first_name': sender.first_name,
                        'last_name': sender.last_name
                    }
                except User.DoesNotExist:
                    msg['sender'] = None
            
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='join')
    def join_channel(self, request, pk=None):
        """Join a public channel"""
        try:
            channel = ChannelMongoService.get_channel(pk)
            
            if not channel:
                return Response({'error': 'Channel not found'}, status=status.HTTP_404_NOT_FOUND)
            
            if not channel.get('is_public'):
                return Response({'error': 'This is a private channel'}, status=status.HTTP_403_FORBIDDEN)
            
            success = ChannelMongoService.add_member(pk, request.user.id)
            
            if success:
                return Response({'message': 'Joined channel successfully'})
            else:
                return Response({'message': 'Already a member'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], url_path='leave')
    def leave_channel(self, request, pk=None):
        """Leave a channel"""
        try:
            success = ChannelMongoService.remove_member(pk, request.user.id)
            
            if success:
                return Response({'message': 'Left channel successfully'})
            else:
                return Response({'error': 'You are not a member of this channel'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_user_details(self, user_ids):
        """Helper to get user details"""
        users = User.objects.filter(id__in=user_ids)
        return [{
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        } for user in users]
