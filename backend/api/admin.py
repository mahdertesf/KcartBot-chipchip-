from django.contrib import admin
from .models import User, Product, Inventory, Order, OrderItem, CompetitorPrice

# Register your models here.
admin.site.register(User)
admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(CompetitorPrice)
