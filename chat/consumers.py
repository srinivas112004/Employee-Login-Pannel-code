"""
WebSocket Consumers for Chat System
Day 13: Real-time Chat with WebSockets + MongoDB
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
from bson import ObjectId
from .mongo_service import MessageMongoService, OnlineStatusMongoService
from authentication.models import User


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope.get('user')
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update online status
        await self.update_online_status(True)
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name(),
                'timestamp': datetime.utcnow().isoformat(),
            }
        )
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Update online status
        await self.update_online_status(False)
        
        # Notify others that user left
        if hasattr(self, 'room_group_name') and hasattr(self, 'user'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name(),
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_chat_message(data)
            elif message_type == 'typing_start':
                await self.handle_typing_start()
            elif message_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'reaction':
                await self.handle_reaction(data)
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def handle_chat_message(self, data):
        """
        Handle incoming chat message
        """
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return
        
        # Save message to MongoDB
        message_data = await self.save_message(message_text)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': {
                    'id': str(message_data['_id']),
                    'room_id': self.room_id,
                    'sender_id': str(self.user.id),
                    'sender_name': self.user.get_full_name(),
                    'sender_email': self.user.email,
                    'content': message_text,
                    'timestamp': message_data['created_at'].isoformat(),
                    'is_edited': False,
                    'read_by': [],
                }
            }
        )
    
    async def handle_typing_start(self):
        """
        Handle typing indicator start
        """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name(),
                'is_typing': True,
            }
        )
    
    async def handle_typing_stop(self):
        """
        Handle typing indicator stop
        """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name(),
                'is_typing': False,
            }
        )
    
    async def handle_read_receipt(self, data):
        """
        Handle message read receipt
        """
        message_id = data.get('message_id')
        
        if message_id:
            # Update read status in MongoDB
            await self.mark_message_read(message_id)
            
            # Notify others
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name(),
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
    
    async def handle_reaction(self, data):
        """
        Handle message reaction (emoji)
        """
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if message_id and emoji:
            # Save reaction to MongoDB
            await self.add_reaction(message_id, emoji)
            
            # Notify others
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message_id,
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name(),
                    'emoji': emoji,
                    'timestamp': datetime.utcnow().isoformat(),
                }
            )
    
    # Event handlers for group messages
    
    async def chat_message(self, event):
        """
        Send chat message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'message',
            'data': event['message']
        }))
    
    async def typing_indicator(self, event):
        """
        Send typing indicator to WebSocket
        """
        # Don't send typing indicator to self
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing'],
            }))
    
    async def user_join(self, event):
        """
        Notify when user joins room
        """
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user_id': event['user_id'],
                'username': event['username'],
                'timestamp': event['timestamp'],
            }))
    
    async def user_leave(self, event):
        """
        Notify when user leaves room
        """
        if event['user_id'] != str(self.user.id):
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'username': event['username'],
                'timestamp': event['timestamp'],
            }))
    
    async def read_receipt(self, event):
        """
        Send read receipt to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))
    
    async def message_reaction(self, event):
        """
        Send message reaction to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'reaction',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'emoji': event['emoji'],
            'timestamp': event['timestamp'],
        }))
    
    async def file_uploaded(self, event):
        """
        Notify when file is uploaded
        """
        await self.send(text_data=json.dumps({
            'type': 'file_upload',
            'file_data': event['file_data'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
        }))
    
    # Database operations
    
    @database_sync_to_async
    def save_message(self, content):
        """
        Save message to MongoDB
        """
        service = MessageMongoService()
        user_data = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        message_data = {
            'room_id': self.room_id,
            'sender_id': self.user.id,
            'content': content,
            'message_type': 'text',
        }
        
        return service.create_message(message_data, user_data)
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """
        Mark message as read in MongoDB
        """
        service = MessageMongoService()
        return service.mark_as_read(message_id, self.user.id)
    
    @database_sync_to_async
    def add_reaction(self, message_id, emoji):
        """
        Add reaction to message in MongoDB
        """
        service = MessageMongoService()
        return service.add_reaction(message_id, self.user.id, emoji)
    
    @database_sync_to_async
    def update_online_status(self, is_online):
        """
        Update user's online status in MongoDB
        """
        service = OnlineStatusMongoService()
        if is_online:
            service.set_online(self.user.id)
        else:
            service.set_offline(self.user.id)


class OnlineStatusConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for tracking online users
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        self.user = self.scope.get('user')
        
        # Verify user is authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        self.group_name = 'online_users'
        
        # Join online users group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update online status
        await self.update_online_status(True)
        
        # Send current online users list
        online_users = await self.get_online_users()
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))
        
        # Notify others that user is online
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_status_change',
                'user_id': str(self.user.id),
                'username': self.user.get_full_name(),
                'is_online': True,
            }
        )
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        # Update online status
        await self.update_online_status(False)
        
        # Notify others that user is offline
        if hasattr(self, 'group_name') and hasattr(self, 'user'):
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_status_change',
                    'user_id': str(self.user.id),
                    'username': self.user.get_full_name(),
                    'is_online': False,
                }
            )
            
            # Leave group
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def user_status_change(self, event):
        """
        Send user status change to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'status_change',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online'],
        }))
    
    @database_sync_to_async
    def update_online_status(self, is_online):
        """
        Update user's online status in MongoDB
        """
        service = OnlineStatusMongoService()
        if is_online:
            service.set_online(self.user.id)
        else:
            service.set_offline(self.user.id)
    
    @database_sync_to_async
    def get_online_users(self):
        """
        Get list of currently online users
        """
        service = OnlineStatusMongoService()
        statuses = service.get_online_users()
        return [{
            'user_id': str(status['user_id']),
            'last_seen': status['last_seen'].isoformat() if status.get('last_seen') else None,
        } for status in statuses]


class ChannelBroadcastConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for channel broadcasts
    Handles real-time notifications for department/project channels
    """
    
    async def connect(self):
        """
        Handle WebSocket connection for channel
        """
        self.user = self.scope.get('user')
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel_group_name = f'channel_{self.channel_id}'
        
        # Verify authentication
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        # Verify channel access
        has_access = await self.check_channel_access()
        if not has_access:
            await self.close()
            return
        
        # Join channel group
        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Connected to channel {self.channel_id}'
        }))
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'channel_group_name'):
            await self.channel_layer.group_discard(
                self.channel_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Handle incoming WebSocket messages
        (Channels typically don't allow user messages - read-only broadcasts)
        """
        pass
    
    async def broadcast_message(self, event):
        """
        Send broadcast message to WebSocket
        """
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'data': event['data'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp'],
        }))
    
    async def channel_update(self, event):
        """
        Notify about channel updates (name, description, settings)
        """
        await self.send(text_data=json.dumps({
            'type': 'channel_update',
            'update_type': event['update_type'],
            'data': event['data'],
        }))
    
    @database_sync_to_async
    def check_channel_access(self):
        """
        Check if user has access to channel
        """
        from .mongo_service import ChannelMongoService
        
        channel = ChannelMongoService.get_channel(self.channel_id)
        
        if not channel or not channel.get('is_active'):
            return False
        
        # Allow if public, member, or admin
        if channel.get('is_public'):
            return True
        
        if self.user.id in channel.get('members', []):
            return True
        
        if self.user.id in channel.get('admins', []):
            return True
        
        return False
