from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from .models import User, ConversationHistory

class CustomUserCreateSerializer(UserCreateSerializer):
    """Custom user creation serializer that includes the role field."""
    
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')
        extra_kwargs = {
            'password': {'write_only': True}
        }

class CustomUserSerializer(UserSerializer):
    """Custom user serializer that includes the role field."""
    
    class Meta(UserSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'role')


class ConversationHistorySerializer(serializers.ModelSerializer):
    """Serializer for conversation history with order notification support."""
    order_id = serializers.SerializerMethodField()
    
    class Meta:
        model = ConversationHistory
        fields = ('id', 'sender', 'message', 'timestamp', 'message_type', 'order_id')
    
    def get_order_id(self, obj):
        return str(obj.order.order_id) if obj.order else None
