from django.contrib import admin
from .models import Category, Product, ProductImage, Order, OrderItem, InventoryItem, Cart, CartItem
# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(InventoryItem)
admin.site.register(Cart)
admin.site.register(CartItem)