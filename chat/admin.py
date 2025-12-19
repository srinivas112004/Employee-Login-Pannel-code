from django.contrib import admin
from .models import ChatRoom, Message, UserOnlineStatus, ChatNotification


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'room_type', 'participant_count', 'created_by', 'created_at', 'is_active']
    list_filter = ['room_type', 'is_active', 'created_at']
    search_fields = ['name', 'room_identifier', 'description', 'participants__email']
    readonly_fields = ['room_identifier', 'created_at', 'updated_at', 'participant_count']
    filter_horizontal = ['participants']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'room_type', 'room_identifier', 'description', 'avatar')
        }),
        ('Participants', {
            'fields': ('participants', 'created_by', 'participant_count')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'sender', 'message_type', 'content_preview', 'timestamp', 'is_read', 'deleted']
    list_filter = ['message_type', 'is_read', 'deleted', 'timestamp']
    search_fields = ['content', 'sender__email', 'room__name']
    readonly_fields = ['timestamp', 'edited_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(UserOnlineStatus)
class UserOnlineStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_online', 'last_seen', 'status_message']
    list_filter = ['is_online', 'last_seen']
    search_fields = ['user__email', 'status_message']
    readonly_fields = ['last_seen']


@admin.register(ChatNotification)
class ChatNotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'room', 'message_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__email', 'room__name']
    readonly_fields = ['created_at']
    
    def message_preview(self, obj):
        return obj.message.content[:30]
    message_preview.short_description = 'Message'

