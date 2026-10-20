from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import UserUpdateTracker

from django.contrib.auth import get_user_model
User = get_user_model()  


@receiver(post_save, sender=User)
def update_last_updated_on_save(sender, instance, **kwargs):
    UserUpdateTracker.update_timestamp()


@receiver(post_delete, sender=User)
def update_last_updated_on_delete(sender, instance, **kwargs):
    UserUpdateTracker.update_timestamp()
    
    

@receiver(post_save, sender=User)
def update_user_isupdate(sender, instance, **kwargs):
    if not instance.is_updated:
        instance.is_updated = True
        instance.save(update_fields=['is_updated'])
        

