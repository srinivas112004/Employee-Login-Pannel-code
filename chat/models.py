from django.db import models
from django.utils import timezone
from authentication.models import User


class ChatRoom(models.Model):
    """Chat room for one-on-one or group conversations"""
    ROOM_TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('department', 'Department Chat'),
        ('project', 'Project Chat'),
    ]
    
    name = models.CharField(max_length=255, help_text="Room name (for groups)")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='direct')
    participants = models.ManyToManyField(User, related_name='chat_rooms', help_text="Users in this chat room")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # For direct messages, store unique identifier
    room_identifier = models.CharField(max_length=255, unique=True, help_text="Unique identifier for the room")
    
    # Metadata
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='chat/avatars/', null=True, blank=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['room_identifier']),
            models.Index(fields=['room_type']),
        ]
    
    def __str__(self):
        return self.name or f"{self.room_type.title()} - {self.room_identifier}"
    
    @property
    def participant_count(self):
        return self.participants.count()
    
    def get_last_message(self):
        """Get the last message in this room"""
        return self.messages.order_by('-timestamp').first()


class Message(models.Model):
    """Individual chat messages stored in PostgreSQL"""
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('file', 'File'),
        ('image', 'Image'),
        ('system', 'System Message'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField(help_text="Message content or file path")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # File attachments
    file = models.FileField(upload_to='chat/files/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Message status
    is_read = models.BooleanField(default=False)
    read_by = models.ManyToManyField(User, related_name='read_messages', blank=True)
    
    # Reactions and metadata
    edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted = models.BooleanField(default=False)
    
    # Reply to another message
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['room', 'timestamp']),
            models.Index(fields=['sender', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}"
    
    def mark_as_read(self, user):
        """Mark message as read by a user"""
        self.read_by.add(user)
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class UserOnlineStatus(models.Model):
    """Track user online/offline status for chat"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='online_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    status_message = models.CharField(max_length=100, blank=True, help_text="Custom status message")
    
    class Meta:
        verbose_name_plural = "User Online Statuses"
    
    def __str__(self):
        status = "Online" if self.is_online else f"Last seen {self.last_seen}"
        return f"{self.user.email} - {status}"
    
    def set_online(self):
        """Set user as online"""
        self.is_online = True
        self.save(update_fields=['is_online', 'last_seen'])
    
    def set_offline(self):
        """Set user as offline"""
        self.is_online = False
        self.save(update_fields=['is_online', 'last_seen'])


class ChatNotification(models.Model):
    """Notifications for unread messages"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_notifications')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.email} - Room: {self.room.name}"
