from typing import List, Dict, Any
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from . import BaseExporter
from ..services.export_registry import register_exporter


@register_exporter('clients')
class ClientExporter(BaseExporter):
    """Exportador de clientes con resumen de servicios"""
    
    def get_data(self) -> List[Dict[str, Any]]:
        try:
            from apps.accounting.models import Client, ClientService
            from django_tenants.utils import connection
            
            tenant = connection.tenant
            if not tenant or tenant.schema_name == 'public':
                return []
            
            clients = Client.objects.filter(is_active=True).prefetch_related('services')
            data = []
            
            for client in clients:
                # Estadísticas de servicios para este cliente
                services_stats = client.services.filter(is_active=True).aggregate(
                    total_servicios=Count('id'),
                    valor_total=Sum('price'),
                    valor_promedio=Avg('price')
                )
                
                client_data = self.serialize_model_instance(client)
                
                # Agregar estadísticas de servicios
                client_data.update({
                    'total_servicios': services_stats['total_servicios'] or 0,
                    'valor_total_servicios': float(services_stats['valor_total'] or 0),
                    'valor_promedio_servicios': float(services_stats['valor_promedio'] or 0),
                })
                
                data.append(client_data)
            
            return data
            
        except Exception as e:
            print(f"Error exporting clients: {e}")
            return []
    
    @classmethod
    def get_display_name(cls) -> str:
        return "Clientes"


@register_exporter('services')
class ServiceExporter(BaseExporter):
    """Exportador de servicios de clientes"""
    
    def get_data(self) -> List[Dict[str, Any]]:
        try:
            from apps.accounting.models import ClientService
            from django_tenants.utils import connection
            
            tenant = connection.tenant
            if not tenant or tenant.schema_name == 'public':
                return []
            
            services = ClientService.objects.filter(is_active=True).select_related('client')
            return self.serialize_queryset(services)
            
        except Exception as e:
            print(f"Error exporting services: {e}")
            return []
    
    @classmethod
    def get_display_name(cls) -> str:
        return "Servicios"


@register_exporter('payments')
class PaymentExporter(BaseExporter):
    """Exportador de pagos de servicios"""
    
    def get_data(self) -> List[Dict[str, Any]]:
        try:
            from apps.accounting.models import ServicePayment
            from django_tenants.utils import connection
            
            tenant = connection.tenant
            if not tenant or tenant.schema_name == 'public':
                return []
            
            payments = ServicePayment.objects.all().select_related('client_service', 'client_service__client')
            return self.serialize_queryset(payments)
            
        except Exception as e:
            print(f"Error exporting payments: {e}")
            return []
    
    @classmethod
    def get_display_name(cls) -> str:
        return "Pagos"
