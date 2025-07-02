from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

def update_business_line_on_service_change(sender, instance, **kwargs):
    """
    Actualiza el estado de la línea de negocio cuando un servicio cambia
    """
    if instance.business_line:
        instance.business_line.update_active_status()

def update_business_line_on_service_delete(sender, instance, **kwargs):
    """
    Actualiza el estado de la línea de negocio cuando se elimina un servicio
    """
    if instance.business_line:
        instance.business_line.update_active_status()

def register_signals():
    """
    Registra las señales de forma segura para evitar problemas de importación circular
    """
    from apps.accounting.models import ClientService
    
    post_save.connect(update_business_line_on_service_change, sender=ClientService)
    post_delete.connect(update_business_line_on_service_delete, sender=ClientService)
