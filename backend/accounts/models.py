from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import random
from django.utils.dateparse import parse_datetime
import string


def generate_unique_code():
    length = 8
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not User.objects.filter(discount_code=code).exists():
            return code

class UserQuerySet(models.QuerySet):
    
    def soft_delete(self):
        return self.update(is_deleted=True)
    
    def hard_delete(self):
        return super(UserQuerySet, self).delete()

class UserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)
    
    def generate_unique_discount_code(self):
        discount_code = ''.join(random.choices(string.ascii_letters, k=8))
        while User.objects.filter(discount_code=discount_code).exists():
            discount_code = ''.join(random.choices(string.ascii_letters, k=8))
        return discount_code
    
    def create_user(self, password=None, **extra_fields):
        """create and save new user"""
        print("in create function")

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, password, **extra_fields):
        print("in superuser function")
        user = self.create_user(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using= self._db)
        return user
     
class User(AbstractBaseUser, PermissionsMixin):
    email= models.EmailField(max_length=200, unique=True, null=True)
    name= models.CharField(max_length=200)
    last_login = models.DateTimeField(('last login'), blank=True, null=True)
    date_joined = models.DateTimeField(('date joined'), default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    address = models.TextField(blank=True, null=True, max_length=400)
    postal_code = models.CharField(max_length=11, blank=True, null=True)
    province = models.CharField(max_length=32, blank=True, null=True)
    city = models.CharField(max_length=32, blank=True, null=True)
    phone_number = models.CharField(null=True,max_length=20, unique=True)
    score = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    is_updated = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False) 
    discount_code = models.TextField(max_length=10, unique=True, null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ["name",]
    
    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def hard_delete(self, *args, **kwargs):
        super(User, self).delete(*args, **kwargs)
        
    def save(self, *args, **kwargs):
        if not self.discount_code:
            self.discount_code = generate_unique_code()
        super().save(*args, **kwargs)
    
class UserUpdateTracker(models.Model):
    last_updated = models.DateTimeField(default=timezone.now)

    @staticmethod
    def get_last_updated():
        tracker, created = UserUpdateTracker.objects.get_or_create(id=1)
        return tracker.last_updated

    @staticmethod
    def set_last_update(date_string):
        last_update = parse_datetime(date_string)
        if last_update is not None:
            tracker, created = UserUpdateTracker.objects.get_or_create(id=1)
            tracker.last_updated = last_update
            tracker.save()
            return True
        return False
    
    @staticmethod
    def update_timestamp():
        tracker, created = UserUpdateTracker.objects.get_or_create(id=1)
        tracker.last_updated = timezone.now()
        tracker.save()
        

class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - ({self.price}$)"
    
class DiscountUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discount = models.ForeignKey(DiscountCode, on_delete=models.CASCADE)
    used = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'discount')

    def __str__(self):
        return f"{self.user} used {self.discount.code}"


