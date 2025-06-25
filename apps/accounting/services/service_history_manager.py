from typing import List, Optional, Dict, Any
from django.db.models import QuerySet
from django.utils import timezone

from apps.accounting.models import ClientService, Client
from apps.business_lines.models import BusinessLine


class ServiceHistoryManager:
    
    @staticmethod
    def get_client_service_history(
        client: Client, 
        business_line: BusinessLine, 
        category: str,
        include_inactive: bool = False
    ) -> QuerySet[ClientService]:
        queryset = ClientService.objects.filter(
            client=client,
            business_line=business_line,
            category=category
        )
        
        if not include_inactive:
            queryset = queryset.filter(is_active=True)
            
        return queryset.select_related('client', 'business_line').order_by('-created')
    
    @staticmethod
    def get_latest_service(
        client: Client, 
        business_line: BusinessLine, 
        category: str
    ) -> Optional[ClientService]:
        return ServiceHistoryManager.get_client_service_history(
            client, business_line, category
        ).first()
    
    @staticmethod
    def get_service_statistics(
        client: Client, 
        business_line: BusinessLine, 
        category: str
    ) -> Dict[str, Any]:
        services = ServiceHistoryManager.get_client_service_history(
            client, business_line, category
        )
        
        total_services = services.count()
        active_services = services.filter(
            payments__status='PAID',
            payments__period_end__gte=timezone.now().date()
        ).distinct().count()
        
        return {
            'total_services': total_services,
            'active_services': active_services,
            'services_with_payments': services.filter(payments__isnull=False).count(),
            'latest_service': services.first()
        }
    
    @staticmethod
    def can_create_new_service(
        client: Client, 
        business_line: BusinessLine, 
        category: str
    ) -> bool:
        return True
    
    @staticmethod
    def get_client_service_history(client, business_line=None, category=None, accessible_lines=None):
        from apps.accounting.models import ClientService
        
        queryset = ClientService.objects.filter(client=client)
        
        if accessible_lines:
            queryset = queryset.filter(business_line__in=accessible_lines)
        elif business_line:
            queryset = queryset.filter(business_line=business_line)
            
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset.select_related('client', 'business_line').prefetch_related('payments').order_by('-created')
    
    @staticmethod
    def get_related_services(client, business_line, category, exclude_service=None):
        from apps.accounting.models import ClientService
        
        queryset = ClientService.objects.filter(
            client=client,
            business_line=business_line,
            category=category
        ).select_related('business_line').order_by('-created')
        
        if exclude_service:
            queryset = queryset.exclude(id=exclude_service.id)
            
        return queryset[:5]
