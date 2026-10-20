from django.contrib import admin
from .models import User, DiscountUsage, DiscountCode

class UserAdmin(admin.ModelAdmin):
    
    def delete_model(self, request, obj):
        obj.is_deleted = True
        obj.save()

    def delete_queryset(self, request, queryset):
        queryset.update(is_deleted=True)

admin.site.register(User, UserAdmin)
admin.site.register(DiscountUsage)
admin.site.register(DiscountCode)