from django.urls import path, include
from .views import (
    InventoryItemAfterSellUpdateView,
    OrderDetailView,
    OrderItemCreateView,
    OrderItemListView,
    ProductListView, 
    ProductDetailView, 
    ProductDetailUpdateView,
    ProductCreateView, 
    ProductCatListView,
    CategoryListView,
    ProductImagesList,
    ProductImageDelete,
    ProductImageUpload,
    BulkDeleteProductsView,
    OrderListView,
    BulkDeleteOrdersView,
    OrderProductlist,
    OrderDetailUpdateView,
    InventoryItemListView,
    InventoryItemCreateView,
    InventoryItemDetailUpdateView,
    InventoryItemDelete,
    InventoryItemDetailView,
    ProductDetailIdView,
    OrderCreateView,
    SalesMetrics,
    HealthCheckView,
    InventoryItemEshopListView,
    ProductFilterListView,
    CategorySameParentListView,
    CartItemListView,
    UpdateCartItemView,
    AddToCartView,
    ZarinpalRequestView,
    ZarinpalVerifyView,
    CheckInventoryView,
    UpdateCartView,
    ProductDetailIdEshopView,
)

urlpatterns = [
    #productimages
    path('products/images/<int:product_id>', ProductImagesList.as_view(), name='product-image-list'),
    path('products/images/delete', ProductImageDelete.as_view(), name='product-image-delete'),
    path('products/images/upload', ProductImageUpload.as_view(), name='product-image-upload'),
    
    #productitems
    path("inventoryitem/<int:product_id>", InventoryItemListView.as_view(), name="inventoryitem"),
    path("inventoryitem/shop/<int:product_id>", InventoryItemEshopListView.as_view(), name="inventoryitemeshop"),
    path("inventoryitem/update/<int:id>", InventoryItemDetailUpdateView.as_view(), name="inventoryitem_detail_update"),
    path("inventoryitem/updateaftersell/<int:id>", InventoryItemAfterSellUpdateView.as_view(), name="inventoryitem_detail_update_aftersell"),
    path("inventoryitem/detail/<str:barcode>", InventoryItemDetailView.as_view(), name="InventoryItem_detail"),
    path("inventoryitem/create", InventoryItemCreateView.as_view(), name="inventoryitem_create"),
    path("inventoryitem/delete", InventoryItemDelete.as_view(), name="inventoryitem_delete"),
    
    #product
    path("products/", ProductListView.as_view(), name="products"),
    path("product_list/", ProductFilterListView.as_view(), name="productsfilter"),
    path("products/update/<slug:slug>", ProductDetailUpdateView.as_view(), name="products_detail_update"),
    path("products/detail/<str:subject>", ProductDetailView.as_view(), name="products_detail"),
    path("products/detailbyid/<int:id>", ProductDetailIdView.as_view(), name="products_detail_id"),
    path("products/detailbyideshop/<int:id>", ProductDetailIdEshopView.as_view(), name="products_detail_id"),
    path("products/create", ProductCreateView.as_view(), name="products_create"),
    path("products/delete", BulkDeleteProductsView.as_view(), name="products_delete"),
    
    #category
    path("products/category/<str:category>", ProductCatListView.as_view(), name="products_cat"),
    path("category/", CategoryListView.as_view(), name="category"),
    path("categoryfliter/", CategorySameParentListView.as_view(), name="categoryfilter"),
    
    #order
    path(r"orders/", OrderListView.as_view(), name="order_list"),
    path("orders/delete", BulkDeleteOrdersView.as_view(), name="orders_delete"),
    path("orders/order_product/", OrderProductlist.as_view(), name="order_product_list"),
    path("orders/order_update/<str:ordercode>/", OrderDetailUpdateView.as_view(), name="order_detail_update"),
    path("orders/order_detail/<str:ordercode>/", OrderDetailView.as_view(), name="order_detail"),
    path("orders/order_create/", OrderCreateView.as_view(), name="order_create"),
    path("orders/order_item_list/<int:order>/", OrderItemListView.as_view(), name="order_item_list"),
    path("orders/order_item_create/", OrderItemCreateView.as_view(), name="order_item_create"),
    path("orders/delete/", BulkDeleteOrdersView.as_view(), name="orders_delete"),
    path("orders/salesmetrics/", SalesMetrics.as_view(), name="sales_metrics"),    
    
    #cart
    path("cartlist/", CartItemListView.as_view(), name="cart_list"),
    path("cartlist/update/<int:id>/", UpdateCartItemView.as_view(), name="cart_item_update"),
    path("cartlist/create/", AddToCartView.as_view(), name="cart_item_create"),
    path("cartlist/check/", CheckInventoryView.as_view(), name="cart_item_check"),
    path("cart/update/", UpdateCartView.as_view(), name="cart_update"),
    
    #payment
    path("payment/request/", ZarinpalRequestView.as_view(), name="payment_create"),
    path("payment/verify/", ZarinpalVerifyView.as_view(), name="payment_verify"),
    
    
    path("health/", HealthCheckView.as_view(), name="health_check"),    
]
