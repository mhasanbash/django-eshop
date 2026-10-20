import unicodedata
from django.forms import ValidationError
from rest_framework.generics import (
    RetrieveAPIView, 
    RetrieveUpdateAPIView, 
    ListAPIView, 
    CreateAPIView, 
    UpdateAPIView
)
from .models import (
    Product, 
    Category, 
    ProductImage,
    Order,
    OrderItem,
    InventoryItem,
    Cart,
    CartItem
)
from accounts.models import (
    DiscountCode,
    DiscountUsage
)
from .serializers import (
    InventoryItemUpdateAfterSellSerializer,
    ProductCreateSerializer,
    ProductSerializer, 
    CategorySerializer, 
    ProductImageSerializer, 
    ProductUpdateSerializer,
    OrderSerializer,
    OrderItemSerializer,
    OrderUpdateSerializer,
    InventoryItemSerializer,
    InventoryItemUpdateSerializer,
    InventoryItemEshopSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
    CartUpdateSerializer,
    ProductEshopSerializer
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncYear
from django.db.models import F, Sum, ExpressionWrapper, FloatField
from django.http import JsonResponse
from django.db import connections, OperationalError
from rest_framework import status, permissions
import jdatetime
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
import requests
from django.db import transaction
from django.conf import settings
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from pillow_heif import register_heif_opener
from django.core.paginator import Paginator
from .torob_auth import validate_token
from rest_framework.exceptions import AuthenticationFailed


register_heif_opener()

User = get_user_model()

def convert_heic_to_jpeg(image_file):
    from PIL import Image
    import io
    from django.core.files.uploadedfile import InMemoryUploadedFile

    print(f"🔍 Trying to convert: {image_file.name} | size={image_file.size}")

    image = Image.open(image_file)
    print(f"📸 Opened image format: {image.format}, mode: {image.mode}, size: {image.size}")

    output_io = io.BytesIO()
    image.convert("RGB").save(output_io, format="JPEG")
    output_io.seek(0)
    print(f"✅ Converted to JPEG, output size = {len(output_io.getbuffer())} bytes")

    converted_image = InMemoryUploadedFile(
        output_io,
        field_name='image',
        name=image_file.name.rsplit('.', 1)[0] + '.jpg',
        content_type='image/jpeg',
        size=output_io.getbuffer().nbytes,
        charset=None
    )
    return converted_image

#__________________________________________________________________________________________________
# Images product View

class ProductImagesList(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductImageSerializer
    pagination_class = None

    def get_queryset(self):
        product_id = self.kwargs.get('product_id') 
        return ProductImage.objects.filter(product_id=product_id) 
     
class ProductImageDelete(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request):
        image_id = request.data.get('image_id')
        if image_id is None:
            return Response({"error": "Image ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = ProductImage.objects.get(pk=image_id)
            image.delete()
            return Response({"message": "Images successfully deleted"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class ProductImageUpload(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        files = request.FILES.copy()
        data = request.data.copy()

        if 'image' in files:
            image_file = files['image']
            if image_file.name.lower().endswith('.heic'):
                try:
                    converted_image = convert_heic_to_jpeg(image_file)

                    files.setlist('image', [converted_image])
                    data.setlist('image', [converted_image])
                except Exception as e:
                    print(f"❌ Error converting HEIC: {e}")
                    return Response(
                        {"error": "Failed to convert HEIC image."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        request._files = files
        request._full_data = data
        serializer = ProductImageSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(f"❌ Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#_____________________________________________________________________________________________
# Products View

class ProductListView(ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def clean_query(self, query):
        if not query:
            return ""
        return unicodedata.normalize("NFKC", query).strip()
    
    def get_queryset(self):        
        search = self.request.query_params.get('search')

        if search and search.strip() != "":
            print(f"[GET_PRODUCTS] Filtering with search: '{search}'")
            return Product.objects.filter(
            Q(subject__icontains=search)
        ).order_by('-published')
        print("[GET_PRODUCTS] Empty search → return all 'p'")
        
        return Product.objects.all().order_by('-published')

class ProductFilterListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(status='p')

        category = self.request.query_params.get('category')
        color = self.request.query_params.get('color')
        price = self.request.query_params.get('price')
        size = self.request.query_params.get('size')
        order = self.request.query_params.get('order')


        print(f"[GET_PRODUCTS] Filtering with category={category}, color={color}, price={price}, size={size}, order={order}")

        def get_all_child_ids(category):
            ids = []
            for child in category.child.all(): 
                ids.append(child.id)
                ids.extend(get_all_child_ids(child))
            return ids

        if category:
            selected_category = Category.objects.get(id=category)
            all_ids = [selected_category.id] + get_all_child_ids(selected_category)
            queryset = queryset.filter(category__in=all_ids)


        if color:
            queryset = queryset.filter(inventory_items__color=color).distinct()
            
        if size:
            queryset = queryset.filter(inventory_items__size=size).distinct()

        if price:
            queryset = queryset.filter(price__lte=price)
            
        if order:
            if order == "newest":
                order = "-published"
            elif order == "cheapest":
                order = "price"
            else :
                order = "-price"
                
            queryset = queryset.order_by(order)
            
        else:
            queryset = queryset.order_by("-published")

        return queryset
     
class ProductDetailUpdateView(RetrieveUpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductUpdateSerializer
    lookup_field = 'slug'
    permission_classes = [permissions.IsAdminUser]

    def update(self, request, *args, **kwargs):
       files = request.FILES.copy()
       data = request.data.copy()

       if 'image' in files:
           image_file = files['image']
           if image_file.name.lower().endswith('.heic'):
               try:
                   converted_image = convert_heic_to_jpeg(image_file)
                   files.setlist('image', [converted_image])
                   data.setlist('image', [converted_image]) 

               except Exception as e:
                   print(f"Conversion error: {e}")
                   return Response({"error": str(e)}, status=400)


       request._files = files
       request._full_data = data  

       response = super().update(request, *args, **kwargs)
       return response   
          
class ProductDetailView(RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser] 
    serializer_class = ProductSerializer
    lookup_field = "subject"

    def get_queryset(self):
        return Product.objects.all()
    
class ProductDetailIdView(RetrieveAPIView):
    serializer_class = ProductSerializer
    lookup_field = "id"
    permission_classes = [permissions.IsAdminUser] 

    def get_queryset(self):
        return Product.objects.all()
    
class ProductDetailIdEshopView(RetrieveAPIView):
    serializer_class = ProductEshopSerializer
    lookup_field = "id"
    permission_classes = [permissions.AllowAny] 

    def get_queryset(self):
        return Product.objects.filter(status='p')
    
class ProductCreateView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request, *args, **kwargs):
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BulkDeleteProductsView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])
    
        if not ids:
            return Response({'error': 'No IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        products_to_delete = Product.objects.filter(id__in=ids)
        if not products_to_delete:
            return Response({'error': 'No products found with the provided IDs.'}, status=status.HTTP_404_NOT_FOUND)
        
        products_to_delete.delete()

        return Response({'success': f'Deleted {len(products_to_delete)} products successfully.'}, status=status.HTTP_200_OK)

#_______________________________________________________________________________________
# InventoryItem

class InventoryItemListView(ListAPIView):
    permission_classes = [permissions.IsAdminUser] 
    serializer_class = InventoryItemSerializer
    pagination_class = None
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return InventoryItem.objects.filter(product_id=product_id)
        
class InventoryItemEshopListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = InventoryItemEshopSerializer
    pagination_class = None
 
    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return InventoryItem.objects.filter(product_id=product_id)

class InventoryItemDetailUpdateView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAdminUser] 
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemUpdateSerializer
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        print("Request Data:", request.data)
        print("Files Data:", request.FILES)
        return super().update(request, *args, **kwargs)
    
class InventoryItemAfterSellUpdateView(RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAdminUser] 
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemUpdateAfterSellSerializer
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        print("Request Data:", request.data)
        print("Files Data:", request.FILES)
        return super().update(request, *args, **kwargs)

class InventoryItemCreateView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request, *args, **kwargs):
        serializer = InventoryItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class InventoryItemDetailView(RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser] 
    serializer_class = InventoryItemUpdateSerializer
    lookup_field = "barcode"

    def get_queryset(self):
        return InventoryItem.objects.all()
    
class InventoryItemDelete(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request):
        entry_id = request.data.get('entry_id')
        if entry_id is None:
            return Response({"error": "entry ID not provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            entry = InventoryItem.objects.get(pk=entry_id)
            entry.delete()
            return Response({"message": "entry successfully deleted"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#___________________________________________________________________________________________
# Category View
class CategoryListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.filter(parent=None)
    serializer_class = CategorySerializer
    pagination_class = None

class CategorySameParentListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    pagination_class = None
    
    def get_queryset(self):
        queryset = Category.objects.all()

        parentId = self.request.query_params.get('parent')

        print(f"[GET_CATEGORY] Filtering with parentId={parentId}")

        if parentId:
            queryset = queryset.filter(parent=parentId)

        return queryset

class ProductCatListView(ListAPIView):
    permission_classes = [permissions.AllowAny]
    model = Product
    serializer_class = ProductSerializer
    def get_queryset(self):
        category = self.kwargs['category']
        queryset = self.model.objects.filter(category__title = category, status= 'p')
        print(category)
        return queryset
    
#___________________________________________________________________________________________
# Order View
class OrderListView(ListAPIView):
    serializer_class = OrderSerializer 

    def clean_query(self, query):
        if not query:
            return ""
        return unicodedata.normalize("NFKC", query).strip()

    def get_queryset(self):
        user = self.request.user 
        params = self.request.query_params

        status_filter = params.get("status")
        phone_number = params.get("phonNumber")
        shamsi_date = params.get("date")


        if user.is_superuser:
            qs = Order.objects.all().order_by("-modified_at")
        else:
            qs = Order.objects.filter(user=user).order_by("-modified_at")


        if not (status_filter or phone_number or shamsi_date):
            return qs

        # date filter
        if shamsi_date and shamsi_date.strip() != "":
            try:
                shamsi_date = jdatetime.date(*map(int, shamsi_date.split("/")))
                gregorian_date = shamsi_date.togregorian()
                start_datetime = datetime.combine(gregorian_date, datetime.min.time())
                end_datetime = datetime.combine(gregorian_date, datetime.max.time())
                qs = qs.filter(created_at__range=(start_datetime, end_datetime))
            except Exception as e:
                print(f"[WARN] Invalid date format: {e}")

        # phone number filter
        if phone_number and phone_number.strip() != "":
            phone_number = self.clean_query(phone_number)
            qs = qs.filter(customer_phone__icontains=phone_number)

        # status filter
        if status_filter and status_filter.strip() != "":
            qs = qs.filter(status=status_filter)

        return qs
            
class BulkDeleteOrdersView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def post(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])

        if not ids:
            return Response({'error': 'No IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        orderss_to_delete = Order.objects.filter(id__in=ids)
        if not orderss_to_delete:
            return Response({'error': 'No orders found with the provided IDs.'}, status=status.HTTP_404_NOT_FOUND)
        
        orderss_to_delete.delete()

        return Response({'success': f'Deleted {len(orderss_to_delete)} products successfully.'}, status=status.HTTP_200_OK)
 
class OrderProductlist(APIView):
    def get(self, request):
        user = self.request.user 
        order_id = request.GET.get('order_id')

        if not order_id :
            return Response({'error': 'product not found'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_superuser:
            queryset = OrderItem.objects.filter(order_id=order_id)
            serializer = OrderItemSerializer(queryset, many=True)
            return Response(serializer.data)
        else:
            order = get_object_or_404(Order, id=order_id, user=user)
            if order:
                queryset = OrderItem.objects.filter(order=order)
                serializer = OrderItemSerializer(queryset, many=True)
                return Response(serializer.data)
            return Response({'error': 'product not found'}, status=status.HTTP_404_NOT_FOUND)

class OrderDetailUpdateView(UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Order.objects.all()
    serializer_class = OrderUpdateSerializer
    lookup_field = 'ordercode'
    
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
    
class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        ordercode = self.kwargs.get('ordercode')

        if not request.user.is_staff:
            order = get_object_or_404(Order, user=request.user, ordercode=ordercode)
        else:
            order = get_object_or_404(Order, ordercode=ordercode)

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OrderCreateView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    
    def post(self, request, *args, **kwargs):
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderItemCreateView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    
    def post(self, request, *args, **kwargs):
        serializer = OrderItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderItemListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        order_id = self.kwargs.get('order')

        if not request.user.is_staff:
            order = get_object_or_404(Order, user=request.user, id=order_id)
        else:
            order = get_object_or_404(Order, id=order_id)

        items = OrderItem.objects.filter(order=order)
        serializer = OrderItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

#___________________________________________________________________________________________

class SalesMetrics(APIView):
    permission_classes = [permissions.IsAdminUser] 
    def get(self, request):
        sum_raw_price_items = InventoryItem.objects.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('raw_price') * F('shop_quantity'),
                    output_field=FloatField()
                )
            )
        )['total']

        sum_price_items = InventoryItem.objects.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F('price') * F('shop_quantity'),
                    output_field=FloatField()
                )
            )
        )['total']
        
        report_type = request.GET.get('type')
        print(report_type)
        now = timezone.now()

        if(report_type == 'day'):
            daily_data = (
            Order.objects
            .filter(created_at__gte=now - timedelta(days=30))
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum('amount_paid'))
            .order_by('day')
            )
            sum_amount_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=30)).aggregate(total = Sum('amount'))['total']
            sum_amount_raw_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=30)).aggregate(total = Sum('cost_raw'))['total']
            sum_amount_paid_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=30)).aggregate(total = Sum('amount_paid'))['total']

            return Response({
            "total_amount": sum_amount_order_item,
            "total_amount_raw": sum_amount_raw_order_item,
            "total_amount_paid": sum_amount_paid_order_item,
            "daily_sales": daily_data,
            "sum_raw_price_items":sum_raw_price_items,
            "sum_price_items":sum_price_items
            })

        else:
            monthly_data = (
            Order.objects
            .filter(created_at__gte=now - timedelta(days=365))
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum('amount_paid'))
            .order_by('month')
            )
            sum_amount_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=365)).aggregate(total = Sum('amount'))['total']
            sum_amount_raw_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=365)).aggregate(total = Sum('cost_raw'))['total']
            sum_amount_paid_order_item = Order.objects.filter(created_at__gte=now - timedelta(days=365)).aggregate(total = Sum('amount_paid'))['total']
            return Response({
            "total_amount": sum_amount_order_item,
            "total_amount_raw": sum_amount_raw_order_item,
            "total_amount_paid": sum_amount_paid_order_item,
            "monthly_data": monthly_data,
            "sum_raw_price_items":sum_raw_price_items,
            "sum_price_items":sum_price_items
            })
              
#___________________________________________________________________________________________
#health checker

class HealthCheckView(APIView):
    authentication_classes = [] 
    permission_classes = []      

    def get(self, request):
        db_ok = True
        try:
            connections['default'].cursor().execute("SELECT 1")
        except OperationalError:
            db_ok = False

        status_code = 200 if db_ok else 503
        return Response(
            {"status": "ok" if db_ok else "unhealthy"},
            status=status_code
        )

#___________________________________________________________________________________________
#add product to cart
class AddToCartView(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        cart, created = Cart.objects.get_or_create(user=request.user)

        inventory_item_id = request.data.get("inventory_item")
        count = int(request.data.get("count", 1))
        max_count = int(request.data.get("max_count", 1))

        try:
            inventory_item = InventoryItem.objects.get(id=inventory_item_id)
        except InventoryItem.DoesNotExist:
            return Response({"detail": "Invalid inventory item."}, status=status.HTTP_400_BAD_REQUEST)

        existing_item = CartItem.objects.filter(cart=cart, inventoryItem=inventory_item).first()
        if existing_item:
            existing_item.count += count
            existing_item.save()
            serializer = CartItemSerializer(existing_item)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = CartItemSerializer(data={"inventoryItem": inventory_item.id, "cart": cart.id, "count": count, "max_count":max_count})
        if serializer.is_valid():
            serializer.save(cart=cart, inventoryItem=inventory_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class CartItemListView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

        cart = Cart.objects.get_or_create(user=request.user)
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class UpdateCartItemView(UpdateAPIView):
    serializer_class = CartItemUpdateSerializer
    lookup_field = 'id'
    
    def get_queryset(self):
        cart = Cart.objects.get(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)
    
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({"detail": "item deleted succsefully!"}, status=status.HTTP_200_OK)
    
class UpdateCartView(UpdateAPIView):
    serializer_class = CartUpdateSerializer
    
    def get_object(self):
        return Cart.objects.get(user=self.request.user)
    
    def put(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            print("Serializer errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        self.perform_update(serializer)
        return Response(serializer.data)

class ZarinpalRequestView(APIView):

    def post(self, request):
        cart = None
        items = None
        amount = 0
        amount_paid = 0
        cost_raw = 0
        

        ordercode = request.data.get('ordercode')
        neword = None
        with transaction.atomic():
            
            if ordercode:
                neword = Order.objects.get(ordercode=ordercode)
                amount = int(neword.amount * 1000)
                amount_paid = int(neword.amount_paid * 1000)
            else:
                cart = Cart.objects.get(user=request.user)
                items = CartItem.objects.filter(cart=cart)
                
                if (len(items) == 0):
                    return Response(
                        {"status": "failed", "message": "سبد خرید خالی است"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                for item in items:
                    amount += item.inventoryItem.price * item.count
                    cost_raw += item.inventoryItem.raw_price * item.count
                    invitem_obj = item.inventoryItem
                    if invitem_obj.shop_quantity >= item.count:
                        invitem_obj.shop_quantity -= item.count
                        invitem_obj.save()
                    else:
                        return Response(
                            {"status": "failed", "message": "موجودی محصول کافی نیست"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    
                    neword = Order.objects.create(
                        user=request.user,
                        status='o',
                        address=f"{request.user.province} - {request.user.city} - {request.user.address}",
                        customer_phone=request.user.phone_number,
                        online_status='n',
                        deliver=cart.deliver
                    )
                    
                    if(cart.deliver == 't'):
                        neword.deliver_cost = 0
                    elif(cart.deliver == 'p'):
                        neword.deliver_cost = 0
                    else:
                        neword.deliver_cost = 0

                    OrderItem.objects.create(
                        order=neword,
                        inventoryItem=invitem_obj,
                        selling_price=invitem_obj.price,
                        raw_price=invitem_obj.raw_price,
                        count=item.count,
                        name=f"{invitem_obj.product.subject} - {invitem_obj.color} - {invitem_obj.size}" 
                    )
                    
                amount = int(amount * 1000)
                neword.cost_raw=cost_raw
                Cart.objects.filter(user=request.user).delete()
                
        if not ordercode:
            discount_flag = False
            
            discount_code = request.data.get('discount_code')
            
            if  discount_code:
                discount = DiscountCode.objects.filter(code=discount_code, active=True).first()
                if discount:
                    usage = DiscountUsage.objects.filter(user=request.user, discount=discount, used=False).first()
                    if usage:
                        discount_amount = int(discount.price * 1000)
                        amount_paid = max(amount - discount_amount, 0)  
                        usage.used = True
                        usage.save()
                        discount_flag = True
                    
            if discount_flag == False:
                amount_paid = amount
            
   
        neword.amount_raw=amount/1000 
        neword.amount=amount/1000
        neword.amount_paid=amount_paid/1000
        neword.online_status= 'n'
        neword.status= 'o'
        neword.save()        
        
        merchant_id = settings.MERCHANT_ID
        description =  ""
        callback_url = ""
        metadata = {
            "mobile": request.user.phone_number,
        }

        data = {
            "merchant_id": merchant_id,
            "amount": int((amount_paid + neword.deliver_cost*1000 )*10),
            "callback_url": callback_url,
            "description": description,
            "metadata": metadata,
        }

        try:
            response = requests.post(
                "https://payment.zarinpal.com/pg/v4/payment/request.json",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            result = response.json()

            if "data" in result and result["data"].get("code") == 100:
                authority = result["data"]["authority"]
                payment_url = f"https://payment.zarinpal.com/pg/StartPay/{authority}"
                return Response({"url": payment_url}, status=status.HTTP_200_OK)

            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            print("ZARINPAL REQUEST FAILED:", str(e))
            return Response(
                {"error": f"Connection error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
                    
class CheckInventoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = Cart.objects.get(user=request.user)
        items = CartItem.objects.filter(cart=cart)
        unavailable = []
        for item in items:
            if item.inventoryItem.shop_quantity < item.count:
                unavailable.append({
                    "name": item.inventoryItem.product.subject,
                    "available": item.inventoryItem.shop_quantity,
                    "requested": item.count
                })

        if unavailable:
            return Response({
                "ok": False,
                "unavailable": unavailable
            })
        return Response({"ok": True})
    
class ZarinpalVerifyView(APIView):

    def get(self, request):
        authority = request.query_params.get("Authority")
        status_param = request.query_params.get("Status")

        if not authority or not status_param:
            return Response(
                {"status": "failed", "message": "پارامترهای ورودی ناقص هستند."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if status_param != "OK":
            return Response(
                {"status": "failed", "message": "تراکنش ناموفق بود"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        
        ordercode = request.query_params.get("ordercode")
        order = Order.objects.get(user=request.user, ordercode=ordercode)

        order.online_status= 'n'
        order.save()
        
        
        verify_data = {
            "merchant_id": settings.MERCHANT_ID,
            "amount": int((order.amount_paid + order.deliver_cost)*10000), 
            "authority": authority,
        }
        
        print(f"verify_data : {verify_data}")

        try:
            response = requests.post(
                "https://payment.zarinpal.com/pg/v4/payment/verify.json",
                json=verify_data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=10,
            )
            result = response.json()
            data = result.get("data", {})


            code = data.get("code")

            if code == 100:
                order.online_status= 'p'
                order.save()
                Cart.objects.filter(user=request.user).delete()
                return Response( 
                    {
                        "status": "success",
                        "message": "پرداخت با موفقیت انجام شد.",
                        "ref_id": data.get("ref_id"),
                        "card_pan": data.get("card_pan"),
                        "fee": data.get("fee"),
                    },
                    status=status.HTTP_200_OK,
                )

            elif code == 101:
                order.online_status= 'p'
                order.save()
                Cart.objects.filter(user=request.user).delete()
                return Response(
                    {
                        "status": "success",
                        "message": "تراکنش قبلاً تأیید شده است.",
                        "ref_id": data.get("ref_id"),
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                order.status= 'n'
                order.save()
                return Response(
                    {
                        "status": "failed",
                        "code": code,
                        "message": data.get("message", "تراکنش ناموفق بود."),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": f"خطا در ارتباط با زرین‌پال: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
