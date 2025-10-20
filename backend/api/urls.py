from django.urls import path
from .views import ChatAPIView, NotificationAPIView, OrderActionAPIView

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('notifications/', NotificationAPIView.as_view(), name='notifications'),
    path('orders/action/', OrderActionAPIView.as_view(), name='order_action'),
]


