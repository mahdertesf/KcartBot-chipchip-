import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    default_location = models.CharField(max_length=255, blank=True, null=True)
    ROLE_CHOICES = [('customer', 'Customer'), ('supplier', 'Supplier')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    def __str__(self):
        return self.username

class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255)
    internal_name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20)
    photo_url = models.URLField(max_length=500, blank=True, null=True)

class Inventory(models.Model):
    inventory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'supplier'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_available = models.FloatField()
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, default='active')
    available_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    class Meta:
        unique_together = ('supplier', 'product')

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'customer'})
    order_date = models.DateTimeField()
    STATUS_CHOICES = [
        ('pending_acceptance', 'Pending Acceptance'),
        ('accepted', 'Accepted by Supplier'),     
        ('declined', 'Declined by Supplier'),     
        ('out_for_delivery', 'Out for Delivery'),     
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_acceptance')

class OrderItem(models.Model):
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    supplier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'supplier'})
    quantity = models.FloatField()
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)

class CompetitorPrice(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    date = models.DateField()
    competitor_tier = models.CharField(max_length=25)
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        unique_together = ('product', 'date', 'competitor_tier')
        indexes = [models.Index(fields=['date'])]

class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Optional reference to inventory for expiry notifications
    inventory = models.ForeignKey('Inventory', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    notification_type = models.CharField(max_length=50, default='general')  # 'expiry_alert', 'order_update', 'general'

class ConversationHistory(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    SENDER_CHOICES = [('user', 'User'), ('bot', 'Bot')]
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    # Fields for order notifications
    message_type = models.CharField(max_length=50, default='text')  # 'text', 'order_notification', 'order_response'
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)  # Link to order if this is an order message

    class Meta:
        ordering = ['timestamp']