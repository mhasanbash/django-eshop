# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InventoryItem, Product
from django.db import models


def update_product_availability(product):
    entries = product.inventory_items.filter(
        models.Q(shop_quantity__gt=0)
    )
    product.is_available = entries.exists()
    
    first_entry = entries.first()
    if first_entry:
        product.price = first_entry.price
        
    else:
        product.price = 0
    product.save(update_fields=['is_available', 'price'])

@receiver(post_save, sender=InventoryItem)
@receiver(post_delete, sender=InventoryItem)
def update_inventory_item(sender, instance, **kwargs):
    update_product_availability(instance.product)
