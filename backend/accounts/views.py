from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView, ListAPIView, CreateAPIView, UpdateAPIView
from .serializers import UserSerializer, UserUpdateSerializer, UserUpdateSiteSerializer
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import , DiscountCode, DiscountUsage
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.cache import caches
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import generate_otp, hash_code, otp_expiry, send_sms_kavenegar
from django.shortcuts import get_object_or_404
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from datetime import datetime
from django.contrib.auth import logout
from django.db import transaction

User = get_user_model()

def normalize_phone(raw: str) -> str | None:
    if not raw or not isinstance(raw, str):
        return None

    digits = raw.strip()
    
    if (len(digits) != 11):
        return None
    elif ( not digits.startswith('0') ):
        return None
    else:
        national = digits

    return national


class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    @method_decorator(ratelimit(key='ip', rate='10/h', block=False), name='dispatch')
    def post(self, request):
        print("start of prossecig of sending sms ...")
        cache = caches['default']
        phone = request.data.get("phone", "").strip()

        if not phone:
            return Response({"error": "شماره موبایل الزامی است"}, status=400)
        elif normalize_phone(phone) == None:
            return Response({"error": "شماره موبایل اشتباه است"}, status=400)
        
        otp_key = f"otp:{phone}"
        now = timezone.now()
        
        try:
            otp_data = cache.get(otp_key)
            if otp_data:
                attempts = otp_data.get("attempts", 0)
                expires_at = parse_datetime(otp_data.get("expires_at"))
                last_sent = parse_datetime(otp_data.get("last_sent"))
                
                try:
                    last_sent = timezone.make_aware(last_sent)
                except Exception as e:
                    print("cant convert")
                    
                if last_sent and (now - last_sent).total_seconds() < SEND_COOLDOWN_SECONDS:
                    return Response({"error": "لطفاً کمی صبر کنید و دوباره تلاش کنید."}, status=429)

                
                if expires_at and expires_at < now:
                    otp_data = {}
                    attempts = 0
                
            else:
                otp_data = {}
                attempts = 0
            
            data = send_sms_kavenegar(phone)
            
            status = data.get("status")
            if status != "عملیات موفق":
                cache.delete(otp_key)
                logger.warning("SMS provider failed for phone=%s", phone)
                return Response({"error": "ارسال پیامک ناموفق بود"}, status=502)
            
            code_hash = hash_code(data['code'])
            
            otp_data.update({
                "code_hash": code_hash,
                "expires_at": otp_expiry(OTP_TTL_MINUTES).isoformat(),
                "attempts": 0,
                "last_sent": now.isoformat()
            })
            
            cache.set(otp_key, otp_data, timeout=OTP_TTL_MINUTES*60)

        except Exception as e:
            cache.delete(otp_key)
            return Response({"error": f"ارسال پیامک ناموفق بود! {otp_key}"}, status=500)

        return Response({
            "message": "کد تایید ارسال شد",
            "ttl": OTP_TTL_MINUTES*60
        }, status=200)
      
class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        cache = caches['default']
        phone = request.data.get("phone", "").strip()
        code = request.data.get("code", "").strip()
        
        if not phone or not code:
            return Response({"error": "شماره موبایل و کد الزامی هستند"}, status=400)
        
        otp_key = f"otp:{phone}"
        now = timezone.now()
        
        try:
            otp_data = cache.get(otp_key)

            if otp_data:
                
                expires_at = datetime.fromisoformat(otp_data.get('expires_at').replace("Z", "+00:00"))
                
                attempts = otp_data.get("attempts", 0)
                hashCode = otp_data.get("code_hash")
                
                
                if expires_at and expires_at < now:
                    return Response({"error": "کد منقضی شده است!"}, status=429)
                
                if attempts >= MAX_ATTEMPTS:
                    return Response({"error": "تعداد درخواست‌ها بیش از حد مجاز است."}, status=429)
                
                
                elif  hashCode != hash_code(code):
                    otp_data["attempts"] = attempts + 1
                    cache.set(otp_key, otp_data, timeout=OTP_TTL_MINUTES*60)
                    return Response({"error": "کد نادرست است"}, status=400)
                
                print(f"\n\n before create user")
                
                user = User.objects.get_or_create(
                    phone_number=phone,
                    defaults={"name": "بدون نام"}
                )
                
                cache.delete(otp_key)
                
                refresh = RefreshToken.for_user(user)

                return Response({
                    "accessToken": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    "user": UserSerializer(user).data
                }, status=200)
                
            else:
                return Response({"error": "کد معتبر پیدا نشد. دوباره کد بگیرید."}, status=400)
            
        except Exception as e:
            cache.delete(otp_key)
            return Response({"error": "خطا در ارزیابی کد!"}, status=500)

class UserListView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser] 
    
    def get_queryset(self):
        search = self.request.query_params.get('search')
        print(search)
        if search != "":
            return User.objects.filter(
            Q(name__icontains=search) 
        ).order_by('-date_joined') 
        return User.objects.all().order_by('-date_joined')
        
class UserCreateView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save() 
            
            reference_code = request.data.get("reference_code") 
            if reference_code:  
                try:
                    ref_account = User.objects.get(discount_code=reference_code)
                    ref_account.score += 10  
                    ref_account.save()
                except User.DoesNotExist:
                    pass  

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailView(RetrieveAPIView):
    permission_classes = [permissions.IsAdminUser] 
    serializer_class = UserSerializer
    lookup_field = "discount_code"
    queryset = User.objects.all()

class UserDetailPhoneNumberView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    
    def get(self, request ,phone_number):
        print(f"phone_number : {phone_number}")
        if not phone_number :
            print("phone_number is null")
            return Response({'error': 'product not found'}, status=status.HTTP_404_NOT_FOUND)
            
        queryset = User.objects.filter(phone_number=phone_number)
        print(queryset)
        
        if (queryset):
            print("queryset is exist")
            serializer = UserSerializer(queryset, many=True)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print("queryset is not exist")
            return Response({'error': 'user not found'}, status=status.HTTP_404_NOT_FOUND)
    
class BulkDeleteAccountsView(APIView):
    permission_classes = [permissions.IsAdminUser] 
    
    def post(self, request, *args, **kwargs):
        id_deleted = request.data.get('id')
        if not id_deleted:
            return Response({'error': 'No IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        Accounts_to_delete = User.objects.filter(id=id_deleted)
        if not Accounts_to_delete:
            return Response({'error': 'No Accounts found with the provided IDs.'}, status=status.HTTP_404_NOT_FOUND)
        
        Accounts_to_delete.delete()

        return Response({'success': f'Deleted {len(Accounts_to_delete)} Accounts successfully.'}, status=status.HTTP_200_OK)
 
class UserDetailUpdateView(UpdateAPIView):
    permission_classes = [permissions.IsAdminUser] 
    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    lookup_field = 'id'
      
class UserSiteUpdateView(APIView):

    def patch(self, request, *args, **kwargs):
        user = request.user
        serializer = UserUpdateSiteSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({
            "message": "اطلاعات شما با موفقیت بروزرسانی شد",
            "user": serializer.data
        }, status=status.HTTP_200_OK)
    
class GetCurrentUserDetail(RetrieveAPIView):
    serializer_class = UserSerializer
    
    def get_object(self):
        return self.request.user
      
class LogoutView(APIView):

    def post(self, request):
        try:
            logout(request)
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logged out successfully."}, status=200)
        except Exception:
            return Response({"error": "Invalid token"}, status=400)
    
class GetDiscount(APIView):
    def get(self, request, code, *args, **kwargs):
        user = request.user
        
        discount = get_object_or_404(DiscountCode, code=code, active=True)
        usage, created = DiscountUsage.objects.get_or_create(user=user, discount=discount)

        if usage.used:
            return Response({"detail": "این کد قبلاً استفاده شده است."}, status=400)
        else:
            return Response({"price": discount.price})

