"""
MongoDB Service Layer for Chat System
Handles all MongoDB CRUD operations for chat collections
"""

from datetime import datetime
from bson import ObjectId
from pymongo.errors import PyMongoError
from .mongo_utils import get_mongo_collection, CHAT_ROOMS_COLLECTION, MESSAGES_COLLECTION, ONLINE_STATUS_COLLECTION, NOTIFICATIONS_COLLECTION, CHANNELS_COLLECTION


class ChatMongoService:
    """Service class for chat-related MongoDB operations"""
    
    @staticmethod
    def create_chat_room(data):
        """
        Create a new chat room
        
        Args:
            data (dict): {
                'name': str,
                'room_type': str,
                'participants': list[int],  # User IDs
                'created_by': int,
                'identifier': str (optional)
            }
        
        Returns:
            dict: Created chat room document
        """
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        
        room_doc = {
            'name': data.get('name'),
            'room_type': data.get('room_type'),
            'participants': data.get('participants', []),
            'created_by': data.get('created_by'),
            'identifier': data.get('identifier'),
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.insert_one(room_doc)
        room_doc['_id'] = str(result.inserted_id)
        return room_doc
    
    @staticmethod
    def get_chat_room(room_id):
        """Get chat room by ID"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        room = collection.find_one({'_id': ObjectId(room_id)})
        if room:
            room['_id'] = str(room['_id'])
        return room
    
    @staticmethod
    def get_user_chat_rooms(user_id):
        """Get all chat rooms for a user"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        rooms = list(collection.find({
            'participants': user_id,
            'is_active': True
        }).sort('updated_at', -1))
        
        for room in rooms:
            room['_id'] = str(room['_id'])
        return rooms
    
    @staticmethod
    def update_chat_room(room_id, data):
        """Update chat room"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        data['updated_at'] = datetime.now()
        
        result = collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$set': data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def add_participant(room_id, user_id):
        """Add participant to chat room"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$addToSet': {'participants': user_id}, '$set': {'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def remove_participant(room_id, user_id):
        """Remove participant from chat room"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$pull': {'participants': user_id}, '$set': {'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def update_room_participants(room_id, participant_ids):
        """Update all participants in a chat room"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$set': {'participants': participant_ids, 'updated_at': datetime.now()}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    @staticmethod
    def delete_chat_room(room_id):
        """Delete (soft delete) a chat room by setting is_active to False"""
        collection = get_mongo_collection(CHAT_ROOMS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(room_id)},
            {'$set': {'is_active': False, 'updated_at': datetime.now()}}
        )
        return result.modified_count > 0


class MessageMongoService:
    """Service class for message-related MongoDB operations"""
    
    @staticmethod
    def create_message(data):
        """
        Create a new message
        
        Args:
            data (dict): {
                'room_id': str,
                'sender_id': int,
                'content': str,
                'message_type': str,
                'parent_message_id': str (optional)
            }
        
        Returns:
            dict: Created message document
        """
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        message_doc = {
            'room_id': data.get('room_id'),
            'sender_id': data.get('sender_id'),
            'content': data.get('content'),
            'message_type': data.get('message_type', 'text'),
            'parent_message_id': data.get('parent_message_id'),
            'is_edited': False,
            'is_deleted': False,
            'read_by': [],
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.insert_one(message_doc)
        message_doc['_id'] = str(result.inserted_id)
        
        # Update room's last activity
        ChatMongoService.update_chat_room(data.get('room_id'), {'updated_at': datetime.now()})
        
        return message_doc
    
    @staticmethod
    def get_room_messages(room_id, limit=50, skip=0):
        """Get messages for a chat room (paginated)"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        messages = list(collection.find({
            'room_id': room_id,
            'is_deleted': False
        }).sort('created_at', -1).skip(skip).limit(limit))
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        return messages
    
    @staticmethod
    def get_message(message_id):
        """Get message by ID"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        message = collection.find_one({'_id': ObjectId(message_id)})
        if message:
            message['_id'] = str(message['_id'])
        return message
    
    @staticmethod
    def update_message(message_id, content):
        """Update message content"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': {
                'content': content,
                'is_edited': True,
                'updated_at': datetime.now()
            }}
        )
        return result.modified_count > 0
    
    @staticmethod
    def mark_as_read(message_id, user_id):
        """Mark message as read by user"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        try:
            result = collection.update_one(
                {'_id': ObjectId(message_id)},
                {'$addToSet': {'read_by': user_id}}
            )
            # Return True if message was found (matched), even if not modified (already read)
            return result.matched_count > 0
        except Exception as e:
            print(f"Error marking message as read: {str(e)}")
            return False
    
    @staticmethod
    def mark_room_messages_as_read(room_id, user_id):
        """Mark all messages in a room as read"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        result = collection.update_many(
            {'room_id': room_id, 'read_by': {'$ne': user_id}},
            {'$addToSet': {'read_by': user_id}}
        )
        return result.modified_count
    
    @staticmethod
    def delete_message(message_id):
        """Soft delete a message"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(message_id)},
            {'$set': {'is_deleted': True, 'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def search_messages(room_id, query):
        """Search messages in a room"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        messages = list(collection.find({
            'room_id': room_id,
            'content': {'$regex': query, '$options': 'i'},
            'is_deleted': False
        }).sort('created_at', -1).limit(50))
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        return messages
    
    @staticmethod
    def add_reaction(message_id, user_id, emoji):
        """
        Add or update reaction to a message
        
        Args:
            message_id: Message ID
            user_id: User ID who reacted
            emoji: Emoji string
        
        Returns:
            bool: True if successful
        """
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        # Initialize reactions field if it doesn't exist
        collection.update_one(
            {'_id': ObjectId(message_id), 'reactions': {'$exists': False}},
            {'$set': {'reactions': {}}}
        )
        
        # Add user to the emoji's reaction list
        result = collection.update_one(
            {'_id': ObjectId(message_id)},
            {
                '$addToSet': {f'reactions.{emoji}': user_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def remove_reaction(message_id, user_id, emoji):
        """Remove reaction from a message"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(message_id)},
            {
                '$pull': {f'reactions.{emoji}': user_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def create_file_message(data):
        """
        Create a message with file attachment
        
        Args:
            data (dict): {
                'room_id': str,
                'sender_id': int,
                'content': str (optional caption),
                'file_url': str,
                'file_name': str,
                'file_type': str,
                'file_size': int (bytes)
            }
        
        Returns:
            dict: Created message with file metadata
        """
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        message_doc = {
            'room_id': data.get('room_id'),
            'sender_id': data.get('sender_id'),
            'content': data.get('content', ''),
            'message_type': 'file',
            'file_metadata': {
                'file_url': data.get('file_url'),
                'file_name': data.get('file_name'),
                'file_type': data.get('file_type'),
                'file_size': data.get('file_size')
            },
            'is_edited': False,
            'is_deleted': False,
            'read_by': [data.get('sender_id')],
            'reactions': {},
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.insert_one(message_doc)
        message_doc['_id'] = str(result.inserted_id)
        return message_doc
    
    @staticmethod
    def get_room_files(room_id, file_type=None, limit=50, offset=0):
        """
        Get files shared in a room
        
        Args:
            room_id: Room ID
            file_type: Optional filter by file type
            limit: Number of results
            offset: Pagination offset
        
        Returns:
            dict: {'files': list, 'total': int}
        """
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        query = {
            'room_id': room_id,
            'message_type': 'file',
            'is_deleted': False
        }
        
        if file_type:
            query['file_metadata.file_type'] = file_type
        
        total = collection.count_documents(query)
        files = list(collection.find(query)
                    .sort('created_at', -1)
                    .skip(offset)
                    .limit(limit))
        
        for file in files:
            file['_id'] = str(file['_id'])
        
        return {
            'files': files,
            'total': total
        }


class OnlineStatusMongoService:
    """Service class for online status operations"""
    
    @staticmethod
    def set_user_status(user_id, is_online):
        """Set user online/offline status"""
        collection = get_mongo_collection(ONLINE_STATUS_COLLECTION)
        
        status_doc = {
            'user_id': user_id,
            'is_online': is_online,
            'last_seen': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.update_one(
            {'user_id': user_id},
            {'$set': status_doc},
            upsert=True
        )
        return True
    
    @staticmethod
    def set_online(user_id):
        """Set user as online"""
        return OnlineStatusMongoService.set_user_status(user_id, True)
    
    @staticmethod
    def set_offline(user_id):
        """Set user as offline"""
        return OnlineStatusMongoService.set_user_status(user_id, False)
    
    @staticmethod
    def get_user_status(user_id):
        """Get user online status"""
        collection = get_mongo_collection(ONLINE_STATUS_COLLECTION)
        status = collection.find_one({'user_id': user_id})
        if status:
            status['_id'] = str(status['_id'])
        return status
    
    @staticmethod
    def get_online_users(user_ids=None):
        """Get online status for multiple users or all online users"""
        collection = get_mongo_collection(ONLINE_STATUS_COLLECTION)
        
        query = {'is_online': True}
        if user_ids:
            query['user_id'] = {'$in': user_ids}
        
        statuses = list(collection.find(query))
        
        for status in statuses:
            status['_id'] = str(status['_id'])
        return statuses


class NotificationMongoService:
    """Service class for notification operations"""
    
    @staticmethod
    def create_notification(data):
        """Create a new notification"""
        collection = get_mongo_collection(NOTIFICATIONS_COLLECTION)
        
        notification_doc = {
            'user_id': data.get('user_id'),
            'room_id': data.get('room_id'),
            'message_id': data.get('message_id'),
            'notification_type': data.get('notification_type', 'new_message'),
            'is_read': False,
            'created_at': datetime.now()
        }
        
        result = collection.insert_one(notification_doc)
        notification_doc['_id'] = str(result.inserted_id)
        return notification_doc
    
    @staticmethod
    def get_user_notifications(user_id, unread_only=False):
        """Get notifications for a user"""
        collection = get_mongo_collection(NOTIFICATIONS_COLLECTION)
        
        query = {'user_id': user_id}
        if unread_only:
            query['is_read'] = False
        
        notifications = list(collection.find(query).sort('created_at', -1).limit(50))
        
        for notif in notifications:
            notif['_id'] = str(notif['_id'])
        return notifications
    
    @staticmethod
    def mark_as_read(notification_id):
        """Mark notification as read"""
        try:
            collection = get_mongo_collection(NOTIFICATIONS_COLLECTION)
            
            # Validate ObjectId format
            if not ObjectId.is_valid(notification_id):
                print(f"Invalid notification ID format: {notification_id}")
                return False
            
            result = collection.update_one(
                {'_id': ObjectId(notification_id)},
                {'$set': {'is_read': True}}
            )
            
            # Check if notification was found (not if it was modified)
            # Because if it's already read, modified_count will be 0
            if result.matched_count == 0:
                print(f"Notification not found: {notification_id}")
                return False
                
            # Success: notification found and is now marked as read
            return True
        except Exception as e:
            print(f"Error marking notification as read: {str(e)}")
            return False
    
    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all user notifications as read"""
        collection = get_mongo_collection(NOTIFICATIONS_COLLECTION)
        result = collection.update_many(
            {'user_id': user_id, 'is_read': False},
            {'$set': {'is_read': True}}
        )
        return result.modified_count
    
    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications"""
        collection = get_mongo_collection(NOTIFICATIONS_COLLECTION)
        return collection.count_documents({'user_id': user_id, 'is_read': False})


class ChannelMongoService:
    """Service class for channel/broadcast operations"""
    
    @staticmethod
    def create_channel(data):
        """
        Create a department/project channel
        
        Args:
            data (dict): {
                'name': str,
                'channel_type': str (department/project/announcement),
                'description': str,
                'created_by': int,
                'admins': list[int],
                'members': list[int],
                'is_public': bool
            }
        
        Returns:
            dict: Created channel document
        """
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        
        channel_doc = {
            'name': data.get('name'),
            'channel_type': data.get('channel_type', 'department'),
            'description': data.get('description', ''),
            'created_by': data.get('created_by'),
            'admins': data.get('admins', [data.get('created_by')]),
            'members': data.get('members', []),
            'is_public': data.get('is_public', True),
            'is_active': True,
            'settings': {
                'allow_member_posts': data.get('allow_member_posts', True),
                'allow_reactions': data.get('allow_reactions', True),
                'allow_replies': data.get('allow_replies', True)
            },
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.insert_one(channel_doc)
        channel_doc['_id'] = str(result.inserted_id)
        return channel_doc
    
    @staticmethod
    def get_channel(channel_id):
        """Get channel by ID"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        channel = collection.find_one({'_id': ObjectId(channel_id)})
        if channel:
            channel['_id'] = str(channel['_id'])
        return channel
    
    @staticmethod
    def get_user_channels(user_id):
        """Get all channels for a user"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        channels = list(collection.find({
            '$or': [
                {'members': user_id},
                {'admins': user_id},
                {'is_public': True}
            ],
            'is_active': True
        }).sort('updated_at', -1))
        
        for channel in channels:
            channel['_id'] = str(channel['_id'])
        return channels
    
    @staticmethod
    def get_channels_by_type(channel_type):
        """Get channels by type"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        channels = list(collection.find({
            'channel_type': channel_type,
            'is_active': True
        }).sort('name', 1))
        
        for channel in channels:
            channel['_id'] = str(channel['_id'])
        return channels
    
    @staticmethod
    def update_channel(channel_id, data):
        """Update channel"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        data['updated_at'] = datetime.now()
        
        result = collection.update_one(
            {'_id': ObjectId(channel_id)},
            {'$set': data}
        )
        return result.modified_count > 0
    
    @staticmethod
    def add_member(channel_id, user_id):
        """Add member to channel"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(channel_id)},
            {'$addToSet': {'members': user_id}, '$set': {'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def remove_member(channel_id, user_id):
        """Remove member from channel"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(channel_id)},
            {'$pull': {'members': user_id}, '$set': {'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
    
    @staticmethod
    def add_admin(channel_id, user_id):
        """Add admin to channel"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(channel_id)},
            {
                '$addToSet': {'admins': user_id, 'members': user_id},
                '$set': {'updated_at': datetime.now()}
            }
        )
        return result.modified_count > 0
    
    @staticmethod
    def broadcast_message(data):
        """
        Create a broadcast message to channel
        
        Args:
            data (dict): {
                'channel_id': str,
                'sender_id': int,
                'content': str,
                'message_type': str (default: 'text')
            }
        
        Returns:
            dict: Created broadcast message
        """
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        message_doc = {
            'channel_id': data.get('channel_id'),
            'sender_id': data.get('sender_id'),
            'content': data.get('content'),
            'message_type': data.get('message_type', 'text'),
            'is_broadcast': True,
            'is_edited': False,
            'is_deleted': False,
            'read_by': [data.get('sender_id')],
            'reactions': {},
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        result = collection.insert_one(message_doc)
        message_doc['_id'] = str(result.inserted_id)
        return message_doc
    
    @staticmethod
    def get_channel_messages(channel_id, limit=50, offset=0):
        """Get messages from a channel"""
        collection = get_mongo_collection(MESSAGES_COLLECTION)
        
        total = collection.count_documents({
            'channel_id': channel_id,
            'is_deleted': False
        })
        
        messages = list(collection.find({
            'channel_id': channel_id,
            'is_deleted': False
        }).sort('created_at', -1).skip(offset).limit(limit))
        
        for msg in messages:
            msg['_id'] = str(msg['_id'])
        
        return {
            'messages': messages,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def delete_channel(channel_id):
        """Soft delete a channel"""
        collection = get_mongo_collection(CHANNELS_COLLECTION)
        result = collection.update_one(
            {'_id': ObjectId(channel_id)},
            {'$set': {'is_active': False, 'updated_at': datetime.now()}}
        )
        return result.modified_count > 0
