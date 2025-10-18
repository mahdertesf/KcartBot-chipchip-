import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    default_location = models.CharField(max_length=255, blank=True, null=True)
    
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('supplier', 'Supplier'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_date = models.DateField()

    def __str__(self):
        return f"{self.name} ({self.role})"

class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255)
    internal_name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20)
    photo_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.product_name

class Inventory(models.Model):
    inventory_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'supplier'})
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity_available = models.FloatField()
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('sold_out', 'Sold Out'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    available_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ('supplier', 'product')

    def __str__(self):
        return f"{self.product.product_name} by {self.supplier.name} - {self.quantity_available} {self.product.unit}"

class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'customer'})
    order_date = models.DateTimeField()

    STATUS_CHOICES = [
        ('pending', 'Pending Acceptance'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')

    def __str__(self):
        return f"Order {self.order_id} by {self.user.name if self.user else 'Deleted User'}"

class OrderItem(models.Model):
    order_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.FloatField()
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} {self.product.unit} of {self.product.product_name} in Order {self.order_id}"

class CompetitorPrice(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    date = models.DateField()
    
    TIER_CHOICES = [
        ('local_shop', 'Local Shop'),
        ('supermarket', 'Supermarket'),
        ('distribution_center', 'Distribution Center'),
    ]
    competitor_tier = models.CharField(max_length=25, choices=TIER_CHOICES)
    price_per_unit_etb = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('product', 'date', 'competitor_tier')
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.product.product_name} on {self.date} ({self.competitor_tier}): {self.price_per_unit_etb} ETB"