from rest_framework import serializers
from .models import ChatRoom, Message


class MessagesSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ('id','name', 'text', 'timestamp', 'is_read')
        
    def get_name(self, obj):
        if (obj.sender.is_staff):
            return "admin"
        else:
            return obj.sender.phone_number

class ChatSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    last_msg = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
                    
    class Meta:
        model = ChatRoom
        fields = ('id', 'name', 'last_msg', 'user_id', 'is_read', 'last_activity')
        
    def get_name(self, obj):
        if (obj.user.is_staff):
            return "admin"
        else:
            return f"{obj.user.phone_number} - {obj.user.name}"
        
    def get_user_id(self, obj):
        return f"{obj.user.id}"
    
    def get_last_msg(self, obj):
        last_message = Message.objects.filter(room=obj).order_by('-timestamp').first()
        return last_message.text
    
    def get_last_activity(self, obj):
        last_message = Message.objects.filter(room=obj).order_by('-timestamp').first()
        return last_message.timestamp
        
    