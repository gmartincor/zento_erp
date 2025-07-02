from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounting'
    
    def ready(self):
        from apps.accounting.signals import register_signals
        register_signals()
