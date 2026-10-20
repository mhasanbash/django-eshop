from django.urls import path, include
from .views import (
    UserListView,
    UserCreateView,
    UserDetailView,
    BulkDeleteAccountsView,
    UserDetailUpdateView,
    UserDetailPhoneNumberView,
    SendOTPView,
    VerifyOTPView,
    GetCurrentUserDetail,
    UserSiteUpdateView,
    LogoutView,
    GetDiscount,
)

urlpatterns = [
    path(r'acc_list/', UserListView.as_view(), name='account-list'),
    path('acc_create/', UserCreateView.as_view(), name='account-create'),
    path('acc_detail/<str:discount_code>', UserDetailView.as_view(), name='account-detail-discountcode'),
    path('acc_detail_phonenumber/<str:phone_number>/', UserDetailPhoneNumberView.as_view(), name='account-detail-phone_number'),
    path('acc_delete/', BulkDeleteAccountsView.as_view(), name='account-delete'),
    path('acc_update/<int:id>', UserDetailUpdateView.as_view(), name='account-update'),
    
    path("otp/send/", SendOTPView.as_view(), name="otp-send"),
    path("otp/verify/", VerifyOTPView.as_view(), name="otp-verify"),
    path("current_acc/", GetCurrentUserDetail.as_view(), name="current_user"),
    path("current_acc/update/", UserSiteUpdateView.as_view(), name="current_user_update"),
    
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('discount/<str:code>', GetDiscount.as_view(), name='discountCode'),
]