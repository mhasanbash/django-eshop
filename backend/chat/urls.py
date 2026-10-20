from django.urls import path, include
from .views import (
    MessagesListView,
    AdminChatListView,
    MessagesAdminListView
)

urlpatterns = [
    path('msg_list/', MessagesListView.as_view(), name='msg_list'),
    path('chat_list/', AdminChatListView.as_view(), name='chat_list'),
    path('msg_list_user/<int:user_id>', MessagesAdminListView.as_view(), name='msg_list_userId'),

]