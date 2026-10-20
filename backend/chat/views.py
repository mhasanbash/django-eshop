from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ChatRoom, Message
from .serializers import MessagesSerializer, ChatSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import ChatRoom, Message
from .serializers import MessagesSerializer
from django.db.models import Max

class MessagesListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        print(f"self.request.user.id : {self.request.user.id}")
        room = ChatRoom.objects.filter(user_id=self.request.user.id).first()
        print(f"room : {room}")
        if not room:
            return Response({"detail": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(room=room).order_by("timestamp")
        serializer = MessagesSerializer(messages, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

        
class AdminChatListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        rooms = (
            ChatRoom.objects
            .annotate(last_message_time=Max("messages__timestamp"))
            .order_by("-last_message_time")  
            .select_related("user")          
            .prefetch_related("messages")    
        )

        serializer = ChatSerializer(rooms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MessagesAdminListView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, user_id):
        room = ChatRoom.objects.filter(user_id=user_id).first()
        if not room:
            return Response({"detail": "Chat room not found."}, status=status.HTTP_404_NOT_FOUND)

        messages = Message.objects.filter(room=room).order_by("timestamp")
        serializer = MessagesSerializer(messages, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

