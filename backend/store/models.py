from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string
import os


User = get_user_model()

def generate_unique_code():
    length = 8
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Order.objects.filter(ordercode=code).exists():
            return code

def generate_unique_numeric_slug():
    
    slug = ''.join(str(random.randint(0, 9)) for _ in range(8))
    
    while Category.objects.filter(slug=slug).exists():
        slug = ''.join(str(random.randint(0, 9)) for _ in range(8))
    return slug
 
def generate_unique_code():
    length = 8
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Order.objects.filter(ordercode=code).exists():
            return code

    
class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length= 100, unique=True)
    parent = models.ForeignKey('self', default= None, null=True, blank=True, on_delete=models.SET_NULL, related_name='child')
    status = models.BooleanField(default = True)
    
    def __str__(self):
        return self.name
    
    def get_parents(self):
        parents = []
        current = self
        while current:
            parents.append(current.name)
            current = current.parent
        return parents
    
    def get_all_parents(self):
        return list(reversed(self.get_parents()))


class Product(models.Model):
    STATUS_CHOICES = (
        ('p' , 'eshop&shop'),
        ('d' , 'shop'),
    )
    TYPE_CHOICES = (
        ( 'o', 'omde'),
        ('t', 'tak'),
    )
    subject = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        default=generate_unique_numeric_slug,
        
    )
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to = 'images', blank=True)
    published = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length= 1 , choices=STATUS_CHOICES)
    category = models.ForeignKey(Category, blank=True, null=True , on_delete=models.SET_NULL, related_name="product")
    is_available = models.BooleanField(default=False, null=True)
    price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    omde_tak = models.CharField(max_length = 1 , choices=TYPE_CHOICES, null=True, default='o')
    

    def __str__(self):
        return self.subject


class InventoryItem(models.Model):
    product  = models.ForeignKey(Product, on_delete=models.CASCADE,related_name='inventory_items')
    color = models.CharField(max_length=100, null = True)
    size = models.CharField(max_length=32, blank=True)
    barcode = models.CharField(max_length=64,unique=True, default=generate_unique_numeric_slug,)
    shop_quantity = models.PositiveIntegerField(default=0, null = True) 
    price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    raw_price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    discount = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)

    class Meta:
        unique_together = ('product', 'color', 'size')

    def __str__(self):
        return f"{self.product.subject} / {self.color} / {self.size}" 
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='images')
    alt_text = models.CharField(max_length=255, blank=True, null=True)  

    def __str__(self):
        return self.product.subject
    
    def delete(self, *args, **kwargs):
        try:
            if self.image and os.path.isfile(self.image.path):
                os.remove(self.image.path)
        except Exception as e:
            print(f"Failed to delete file {self.image.path}: {e}")
        super().delete(*args, **kwargs)


class Address(models.Model):
    region = models.TextField(max_length=32)
    city = models.TextField(max_length=32)
    addr = models.TextField(max_length=512)
    phone_number = models.TextField(max_length=16)
    reciver = models.TextField(max_length=16)
    

class Order(models.Model):
    STATUS_CHOICES = (
        ('f', 'installments'),
        ('t' , 'cash'),
        ('o' , 'online'),
    )
    
    ONLINE_STATUS_CHOICES = (
        ('f', 'finished'),
        ('t' , 'transfer'),
        ('r' , 'readytosend'),
        ('c' , 'canceled'),
        ('n' , 'notpaying'),
        ('p' , 'pending'),
    )
    
    DELIVER_CHOICES = (
        ('t', 'tipax'),
        ('p' , 'post'),
        ('b' , 'bandar'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    cost_raw = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    amount_raw = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    amount = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    amount_paid = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    status = models.CharField(max_length= 1 , choices=STATUS_CHOICES)
    online_status = models.CharField(max_length= 1 , choices=ONLINE_STATUS_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    modified_at = models.DateTimeField(null=True, blank=True, default=timezone.now)
    address = models.TextField(blank=True, null=True, max_length=400) 
    deliver = models.CharField(max_length= 1 , choices=DELIVER_CHOICES, null=True, blank=True)
    deliver_cost = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    discount_code = models.TextField(max_length=8, null=True, blank=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    ordercode = models.TextField(max_length=8, unique=True, null=True)
    customer_phone= models.TextField(max_length=11, null=True)
    is_online = models.BooleanField(default=False)
    
    def __str__(self):
        return self.ordercode
    
    def save(self, *args, **kwargs):
        if not self.ordercode:
            self.ordercode = generate_unique_code()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order', null=True)
    inventoryItem = models.ForeignKey(InventoryItem, on_delete=models.CASCADE,null=True, related_name="inv_item")
    selling_price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    raw_price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    discount = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    count = models.IntegerField(default=0)
    name = models.CharField(max_length=127, null=True)
    
    def __str__(self):
        return self.order.ordercode


class Cart(models.Model):
    DELIVER_CHOICES = (
        ('t', 'tipax'),
        ('p' , 'post'),
        ('b' , 'bandar'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    deliver = models.CharField(max_length= 1 , choices=DELIVER_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"Cart {self.id} for {self.user.name}"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    inventoryItem = models.ForeignKey(InventoryItem, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)
    max_count = models.PositiveIntegerField(default=1, null=True)

    def __str__(self):
        return f"{self.inventoryItem.product.subject} × {self.count}"

    @property
    def price(self):
        return self.inventoryItem.price
    
    @property
    def name(self):
        return self.inventoryItem.product.subject
    
    @property
    def model(self):
        return f"{self.inventoryItem.size} - {self.inventoryItem.color}" 
    
    @property
    def image(self):
        return self.inventoryItem.product.image
