import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.
    Connects authenticated users to their personal notification channel.
    """
    
    async def connect(self):
        """
        Called when WebSocket connection is established.
        """
        try:
            # Get user from scope (set by AuthMiddleware)
            self.user = self.scope.get('user')
            
            # Only allow authenticated users
            if not self.user or not self.user.is_authenticated:
                print(f"WebSocket connection rejected: user not authenticated")
                await self.close(code=4001)  # Custom close code for authentication failure
                return
            
            # Create a unique group name for this user
            self.user_group_name = f'user_{self.user.id}'
            
            # Join user's personal group
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            # Accept the WebSocket connection
            await self.accept()
            
            print(f"WebSocket connected for user: {self.user.username} (ID: {self.user.id})")
            
            # Send a welcome message
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to KcartBot notifications'
            }))
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close(code=4000)  # Custom close code for server error
    
    async def disconnect(self, close_code):
        """
        Called when WebSocket connection is closed.
        """
        # Leave user's personal group
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """
        Called when a message is received from WebSocket.
        This can be used for ping/pong or other client messages.
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            
            if message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        """
        Called when a notification is sent to the user's group.
        Forwards the notification to the WebSocket client.
        """
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'timestamp': event.get('timestamp', ''),
            'notification_id': event.get('notification_id', '')
        }))
    
    async def chat_message(self, event):
        """
        Called when a chat message is sent to the user's group.
        Forwards the chat message to the WebSocket client.
        """
        # Send chat message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'message_type': event.get('message_type', 'text'),
            'order_id': event.get('order_id', ''),
            'timestamp': event.get('timestamp', '')
        }))

