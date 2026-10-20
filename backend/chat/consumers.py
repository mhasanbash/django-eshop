from channels.generic.websocket import AsyncWebsocketConsumer
import json
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message
from channels.db import database_sync_to_async
from django.utils import timezone
from urllib.parse import parse_qs

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close();
            return

        if user.is_staff:
            query_string = parse_qs(self.scope["query_string"].decode())
            user_id = query_string.get("user_id")[0]
            
            self.user_id = user_id
            self.room_name = f"user_{user_id}"
            self.room_group_name = f"chat_user_{user_id}"
        else:
            self.room_name = f"user_{user.id}"
            self.room_group_name = f"chat_user_{user.id}"


        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        sender = self.scope["user"]
        print(f"message : {message}")
        print(f"sender : {sender}")

        room = None
        sender_name = "admin"
        if sender.is_staff:
            user_id = self.user_id
            room = await self.get_user_room(user_id)
        else:
            room = await self.get_or_create_user_room(sender)
            sender_name = sender.phone_number

        await self.save_message(room, sender, message)

        timestamp = timezone.now().isoformat()
        await self.channel_layer.group_send(
            f"chat_user_{room.user_id}",
            {
                "type": "chat_message",
                "message": message,
                "sender": sender_name,
                "is_read": False,
                "timestamp": timestamp,
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "is_read": event["is_read"],
            "timestamp": event["timestamp"]
        }))

    @database_sync_to_async
    def get_or_create_user_room(self, user):
        room, _ = ChatRoom.objects.get_or_create(user=user)
        return room

    @database_sync_to_async
    def get_user_room(self, user_id):
        room, _ = ChatRoom.objects.get_or_create(user_id=user_id)
        return room
    
    @database_sync_to_async
    def save_message(self, room, sender, msg):
        Message.objects.create(room=room, sender=sender, text=msg)
