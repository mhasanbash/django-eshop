from django.apps import AppConfig
#from django.db.models.signals import post_save, post_delete

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        from . import signals
        # post_save.connect(signals.update_last_updated_on_save)
        # post_delete.connect(signals.update_last_updated_on_delete)
