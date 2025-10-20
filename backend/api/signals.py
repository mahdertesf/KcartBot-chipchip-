from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from api.models import Notification


@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    """
    Signal handler that broadcasts new notifications to users via WebSocket.
    Triggered whenever a Notification is created or updated.
    """
    if created:  # Only broadcast newly created notifications
        try:
            channel_layer = get_channel_layer()
            user_group_name = f'user_{instance.user.id}'
            
            # Send notification to user's WebSocket group
            async_to_sync(channel_layer.group_send)(
                user_group_name,
                {
                    'type': 'notification_message',
                    'message': instance.message,
                    'timestamp': instance.created_at.isoformat(),
                    'notification_id': instance.id
                }
            )
            
            print(f"Notification broadcast to user {instance.user.id}: {instance.message}")
            
        except Exception as e:
            print(f"Error broadcasting notification: {e}")

