from django.db.models import QuerySet, Q, Sum, Count, Avg
from apps.accounting.models import ServicePayment, ClientService


class HistoryService:
    """
    Servicio unificado para manejar diferentes tipos de historiales en el sistema.
    
    Existen dos tipos principales de historiales:
    1. Historial de servicios de un cliente específico (client history)
    2. Historial global de pagos del sistema (payment history)
    """
    
    @staticmethod
    def get_client_services_history(client_id: int, filters: dict = None) -> QuerySet:
        """
        Obtiene el historial de servicios para un cliente específico.
        Usado en: /accounting/clients/{client_id}/services/
        
        Args:
            client_id: ID del cliente
            filters: Filtros opcionales (business_line, category)
        """
        queryset = ClientService.objects.filter(
            client_id=client_id
        ).select_related(
            'client', 'business_line'
        ).prefetch_related('payments').order_by('-created')
        
        if filters:
            if filters.get('business_line'):
                queryset = queryset.filter(business_line_id=filters['business_line'])
            if filters.get('category'):
                queryset = queryset.filter(category=filters['category'])
                
        return queryset
    
    @staticmethod
    def get_global_payments_history(filters: dict = None) -> QuerySet:
        """
        Obtiene el historial global de pagos del sistema.
        Usado en: /accounting/payments/history/
        
        Args:
            filters: Filtros opcionales (business_line, category, service, period)
        """
        queryset = ServicePayment.objects.filter(
            status=ServicePayment.StatusChoices.PAID
        ).select_related(
            'client_service__client',
            'client_service__business_line'
        ).order_by('-payment_date')
        
        if filters:
            if filters.get('business_line'):
                queryset = queryset.filter(
                    client_service__business_line__slug=filters['business_line']
                )
            if filters.get('category'):
                queryset = queryset.filter(
                    client_service__category=filters['category'].upper()
                )
            if filters.get('service_id'):
                queryset = queryset.filter(
                    client_service_id=filters['service_id']
                )
                
        return queryset
    
    @staticmethod
    def get_service_payment_history(service_id: int) -> QuerySet:
        """
        Obtiene el historial de pagos específico para un servicio.
        Usado en: /accounting/services/{service_id}/payment/history/
        
        Args:
            service_id: ID del servicio
        """
        return ServicePayment.objects.filter(
            client_service_id=service_id
        ).order_by('-payment_date')
    
    @classmethod
    def get_history_summary(cls, client_id: int = None, service_id: int = None) -> dict:
        """
        Obtiene un resumen estadístico de historiales.
        """
        summary = {}
        
        if client_id:
            services = cls.get_client_services_history(client_id)
            summary.update({
                'total_services': services.count(),
                'total_revenue': services.aggregate(
                    total=Sum('payments__amount')
                )['total'] or 0,
                'active_services': services.filter(is_active=True).count(),
            })
        
        if service_id:
            payments = cls.get_service_payment_history(service_id)
            summary.update({
                'total_payments': payments.count(),
                'total_paid': payments.aggregate(
                    total=Sum('amount')
                )['total'] or 0,
                'average_payment': payments.aggregate(
                    avg=Avg('amount')
                )['avg'] or 0,
            })
            
        return summary
