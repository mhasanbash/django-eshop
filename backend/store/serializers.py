from rest_framework import serializers
from .models import Product, Category, ProductImage, Order, OrderItem, InventoryItem, Cart, CartItem




class InventoryItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['id','color', 'size', 'shop_quantity', 'price', 'raw_price', 'discount','product_id']
        
class InventoryItemUpdateAfterSellSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['shop_quantity',]
        
class InventoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['id','product' ,'color', 'size', 'shop_quantity', 'barcode', 'price', 'raw_price', 'discount'] 
        
class InventoryItemEshopSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryItem
        fields = ['id','product' ,'color', 'size', 'shop_quantity', 'price', 'discount']              


class ProductUpdateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = ['id', 'subject', 'description', 'status', 'category', 'image']

class ProductSerializer(serializers.ModelSerializer):
    all_parents = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'omde_tak' ,'subject', 'slug', 'description', 'status', 'category', 'image', 'all_parents', 'is_available', 'price']
        
    def get_all_parents(self, obj):
        if obj.category:
            return obj.category.get_all_parents()
            
    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        
class ProductEshopSerializer(serializers.ModelSerializer):
    all_parents = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id','subject', 'omde_tak' ,'slug', 'description', 'category', 'image', 'all_parents', 'is_available', 'price']
        
    def get_all_parents(self, obj):
        if obj.category:
            return obj.category.get_all_parents()
            
    def get_image(self, obj):
        if obj.image:
            return obj.image.url
    
        
class ProductCreateSerializer(serializers.ModelSerializer):
    all_parents = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = ['id','subject', 'slug', 'description', 'status', 'category', 'image', 'all_parents']
        
    def get_all_parents(self, obj):
        if obj.category:
            return obj.category.get_all_parents()
        
        
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = "__all__"
        
        
    def get_children(self, obj):
        children = obj.child.all()
        return CategorySerializer(children, many=True).data

        
class ProductImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image', 'alt_text']
        
        
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"
        
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = "__all__"
        
        
class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("online_status","status", "modified_at", "description", "is_online", "amount_paid")
        

class CartItemSerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'inventoryItem', 'cart', 'count', 'price', 'name', 'image', 'model', 'max_count'] 

    def get_price(self, obj):
        return obj.price

    def get_name(self, obj):
        return obj.name
    
    def get_model(self, obj):
        return obj.model

    def get_image(self, obj):
        image_field = getattr(obj.inventoryItem.product, "image", None)
        if image_field and hasattr(image_field, "url"):
            return image_field.url
        return None
    
class CartItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['count'] 
        
class CartUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['deliver'] 
