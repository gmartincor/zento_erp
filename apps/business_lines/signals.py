from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import BusinessLine
from apps.accounting.models import ClientService


@receiver(post_save, sender=ClientService)
def update_business_line_status_on_service_change(sender, instance, **kwargs):
    instance.business_line.update_active_status()


@receiver(post_delete, sender=ClientService)
def update_business_line_status_on_service_delete(sender, instance, **kwargs):
    instance.business_line.update_active_status()
