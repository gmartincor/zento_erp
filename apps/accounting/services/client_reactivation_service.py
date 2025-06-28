from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db.models import Q, Max

from apps.accounting.models import Client, ClientService


class ClientReactivationService:
    INACTIVE_THRESHOLD_DAYS = 90
    
    @classmethod
    def get_client_status(cls, client: Client) -> Dict[str, Any]:
        active_services = client.services.filter(is_active=True).count()
        
        if active_services > 0:
            return cls._get_active_client_status(client)
        
        last_service = client.services.order_by('-end_date').first()
        if not last_service:
            return cls._get_new_client_status(client)
        
        days_since_last = cls._days_since_last_service(last_service)
        
        if days_since_last <= cls.INACTIVE_THRESHOLD_DAYS:
            return cls._get_recently_inactive_status(client, last_service, days_since_last)
        else:
            return cls._get_long_inactive_status(client, last_service, days_since_last)
    
    @classmethod
    def _get_active_client_status(cls, client: Client) -> Dict[str, Any]:
        return {
            'status': 'active',
            'label': 'Cliente Activo',
            'description': 'Tiene servicios activos en el sistema',
            'action_type': 'renewal',
            'action_label': 'Renovar Servicio',
            'class': 'badge-success',
            'icon': 'check-circle'
        }
    
    @classmethod
    def _get_new_client_status(cls, client: Client) -> Dict[str, Any]:
        return {
            'status': 'new',
            'label': 'Cliente Nuevo',
            'description': 'Sin servicios anteriores en el sistema',
            'action_type': 'create',
            'action_label': 'Crear Primer Servicio',
            'class': 'badge-info',
            'icon': 'plus-circle'
        }
    
    @classmethod
    def _get_recently_inactive_status(cls, client: Client, last_service: ClientService, days: int) -> Dict[str, Any]:
        return {
            'status': 'recently_inactive',
            'label': f'Inactivo {days} días',
            'description': f'Último servicio finalizó hace {days} días',
            'action_type': 'renewal',
            'action_label': 'Renovar Servicio',
            'class': 'badge-warning',
            'icon': 'clock',
            'last_service': last_service
        }
    
    @classmethod
    def _get_long_inactive_status(cls, client: Client, last_service: ClientService, days: int) -> Dict[str, Any]:
        return {
            'status': 'long_inactive',
            'label': f'Inactivo {days} días',
            'description': f'Sin actividad desde hace {days} días',
            'action_type': 'reactivate',
            'action_label': 'Crear Nuevo Servicio',
            'class': 'badge-secondary',
            'icon': 'refresh-cw',
            'last_service': last_service
        }
    
    @classmethod
    def _days_since_last_service(cls, service: ClientService) -> int:
        if not service.end_date:
            return 0
        today = timezone.now().date()
        return (today - service.end_date).days
    
    @classmethod
    def should_prefill_from_service(cls, client: Client) -> Optional[ClientService]:
        status = cls.get_client_status(client)
        if status['status'] in ['recently_inactive', 'long_inactive']:
            return status.get('last_service')
        return None
    
    @classmethod
    def get_clients_by_status(cls, business_line=None) -> Dict[str, int]:
        from django.db.models import Count, Q
        
        queryset = Client.objects.filter(is_deleted=False)
        if business_line:
            queryset = queryset.filter(
                services__business_line__in=business_line.get_descendant_ids()
            ).distinct()
        
        stats = {
            'active': 0,
            'recently_inactive': 0,
            'long_inactive': 0,
            'new': 0
        }
        
        for client in queryset:
            status = cls.get_client_status(client)
            stats[status['status']] += 1
        
        return stats
