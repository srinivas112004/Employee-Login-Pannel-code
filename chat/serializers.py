from rest_framework import serializers
from .models import ChatRoom, Message, UserOnlineStatus, ChatNotification
from authentication.models import User


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for chat"""
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'profile_picture']
        read_only_fields = fields


class UserOnlineStatusSerializer(serializers.ModelSerializer):
    """User online status"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserOnlineStatus
        fields = ['id', 'user', 'user_email', 'user_name', 'is_online', 'last_seen', 'status_message']
        read_only_fields = ['user', 'last_seen']
    
    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.email


class MessageSerializer(serializers.ModelSerializer):
    """Message serializer"""
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()
    sender_avatar = serializers.ImageField(source='sender.profile_picture', read_only=True)
    reply_to_content = serializers.CharField(source='reply_to.content', read_only=True)
    read_by_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'room', 'sender', 'sender_email', 'sender_name', 'sender_avatar',
            'message_type', 'content', 'timestamp', 'file', 'file_name', 'file_size',
            'is_read', 'read_by_count', 'edited', 'edited_at', 'deleted',
            'reply_to', 'reply_to_content'
        ]
        read_only_fields = ['sender', 'timestamp', 'is_read', 'edited', 'edited_at']
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}".strip() or obj.sender.email
    
    def get_read_by_count(self, obj):
        return obj.read_by.count()
    
    def validate(self, data):
        """Validate message data"""
        if data.get('message_type') == 'text' and not data.get('content'):
            raise serializers.ValidationError("Text messages must have content")
        
        if data.get('message_type') in ['file', 'image'] and not data.get('file'):
            raise serializers.ValidationError("File/Image messages must have a file attached")
        
        return data


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages"""
    class Meta:
        model = Message
        fields = ['room', 'message_type', 'content', 'file', 'reply_to']
    
    def validate(self, data):
        """Validate message creation"""
        if data.get('message_type') == 'text' and not data.get('content'):
            raise serializers.ValidationError("Text messages must have content")
        
        return data


class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat room serializer"""
    participants_details = UserBasicSerializer(source='participants', many=True, read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'room_identifier', 'description', 'avatar',
            'participants', 'participants_details', 'participant_count',
            'created_by', 'created_by_email', 'created_at', 'updated_at',
            'is_active', 'last_message', 'unread_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'room_identifier', 'participant_count']
    
    def get_last_message(self, obj):
        """Get last message preview"""
        last_msg = obj.get_last_message()
        if last_msg:
            return {
                'id': last_msg.id,
                'sender_email': last_msg.sender.email,
                'content': last_msg.content[:100],
                'timestamp': last_msg.timestamp,
                'message_type': last_msg.message_type
            }
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(read_by=request.user).exclude(sender=request.user).count()
        return 0


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating chat rooms"""
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="List of user IDs to add as participants"
    )
    
    class Meta:
        model = ChatRoom
        fields = ['name', 'room_type', 'description', 'avatar', 'participants']
    
    def validate_participants(self, value):
        """Validate participants list"""
        if not value:
            raise serializers.ValidationError("At least one participant is required")
        
        # Check if all users exist
        existing_users = User.objects.filter(id__in=value)
        if existing_users.count() != len(value):
            raise serializers.ValidationError("Some users do not exist")
        
        return value
    
    def validate(self, data):
        """Validate room creation"""
        if data.get('room_type') == 'direct' and len(data.get('participants', [])) != 1:
            raise serializers.ValidationError("Direct message rooms must have exactly one other participant")
        
        if data.get('room_type') in ['group', 'department', 'project'] and not data.get('name'):
            raise serializers.ValidationError("Group, department, and project rooms must have a name")
        
        return data
    
    def create(self, validated_data):
        """Create chat room with participants"""
        participants_ids = validated_data.pop('participants')
        request = self.context.get('request')
        
        # Generate room identifier
        if validated_data.get('room_type') == 'direct':
            # For direct messages, create unique identifier based on user IDs
            user_ids = sorted([request.user.id] + participants_ids)
            room_identifier = f"dm_{'_'.join(map(str, user_ids))}"
            
            # Check if room already exists
            existing_room = ChatRoom.objects.filter(room_identifier=room_identifier).first()
            if existing_room:
                return existing_room
        else:
            # For group chats, use timestamp-based identifier
            import uuid
            room_identifier = f"{validated_data['room_type']}_{uuid.uuid4().hex[:12]}"
        
        validated_data['room_identifier'] = room_identifier
        validated_data['created_by'] = request.user
        
        # Create room
        room = ChatRoom.objects.create(**validated_data)
        
        # Add participants
        participants = User.objects.filter(id__in=participants_ids)
        room.participants.add(*participants)
        room.participants.add(request.user)  # Add creator as participant
        
        return room


class ChatNotificationSerializer(serializers.ModelSerializer):
    """Chat notification serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatNotification
        fields = ['id', 'user', 'user_email', 'room', 'room_name', 'message', 'message_preview', 'is_read', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    def get_message_preview(self, obj):
        return {
            'sender': obj.message.sender.email,
            'content': obj.message.content[:50],
            'timestamp': obj.message.timestamp
        }
