from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models import Client, ClientService


class ClientServiceTransactionManager:
    
    @staticmethod
    @transaction.atomic
    def update_client_service(service_instance: ClientService, form_data: Dict[str, Any]) -> ClientService:
        try:
            client = service_instance.client
            ClientServiceTransactionManager._update_client_data(client, form_data)
            ClientServiceTransactionManager._update_service_data(service_instance, form_data)
            
            client.save()
            service_instance.save()
            
            return service_instance
            
        except Exception as e:
            raise ValidationError(f"Error al actualizar cliente y servicio: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def create_client_service(form_data: Dict[str, Any], business_line, category) -> ClientService:
        try:
            client = ClientServiceTransactionManager._get_or_create_client(form_data)
            service = ClientServiceTransactionManager._create_service_from_data(
                client, form_data, business_line, category
            )
            
            service.refresh_from_db()
            
            period_start = form_data.get('period_start')
            period_end = form_data.get('period_end')
            
            if period_start and period_end:
                from .period_service import ServicePeriodManager
                ServicePeriodManager.create_period(
                    client_service=service,
                    period_start=period_start,
                    period_end=period_end,
                    notes="Primer período del servicio"
                )
            
            return service
            
        except Exception as e:
            raise ValidationError(f"Error al crear cliente y servicio: {str(e)}")
    
    @staticmethod
    def _get_or_create_client(form_data: Dict[str, Any]) -> Client:
        dni = form_data['client_dni'].strip().upper()
        
        try:
            client = Client.objects.get(dni=dni, is_deleted=False)
            ClientServiceTransactionManager._update_client_data(client, form_data)
            client.save()
            return client
        except Client.DoesNotExist:
            return ClientServiceTransactionManager._create_client_from_data(form_data)
    
    @staticmethod
    def _update_client_data(client: Client, form_data: Dict[str, Any]) -> None:
        client.full_name = form_data.get('client_name', client.full_name).strip().title()
        client.dni = form_data.get('client_dni', client.dni).strip().upper()
        client.gender = form_data.get('client_gender', client.gender)
        client.email = form_data.get('client_email', client.email or '').strip().lower()
        client.phone = form_data.get('client_phone', client.phone or '').strip()
        client.notes = form_data.get('client_notes', client.notes or '').strip()
        
        if 'client_is_active' in form_data:
            client.is_active = form_data['client_is_active']
        
        if Client.objects.filter(dni=client.dni).exclude(pk=client.pk).exists():
            raise ValidationError(f"Ya existe otro cliente con el DNI {client.dni}")
    
    @staticmethod
    def _update_service_data(service, form_data: Dict[str, Any]) -> None:
        original_is_active = service.is_active
        
        service.price = form_data.get('price', service.price)
        service.start_date = form_data.get('start_date', service.start_date)
        service.admin_status = form_data.get('admin_status', service.admin_status)
        service.is_active = form_data.get('is_active', service.is_active)
        service.notes = form_data.get('notes', service.notes or '').strip()
        
        if 'remanentes' in form_data:
            service.remanentes = form_data['remanentes']
        
        # En el sistema simplificado, todos los servicios BLACK pueden usar remanentes
        if service.category == 'BLACK':
            # Los remanentes se manejan ahora directamente en los períodos de pago
            pass
        
        ClientServiceTransactionManager._handle_service_activation_change(service, original_is_active)
    
    @staticmethod
    def _handle_service_activation_change(service, original_is_active: bool) -> None:
        if original_is_active != service.is_active:
            from .client_state_manager import ClientStateManager
            
            if service.is_active:
                ClientStateManager._unfreeze_service(service, timezone.now().date())
            else:
                ClientStateManager._freeze_service(service, timezone.now().date())
    
    @staticmethod
    def _create_client_from_data(form_data: Dict[str, Any]) -> Client:
        client_data = {
            'full_name': form_data['client_name'].strip().title(),
            'dni': form_data['client_dni'].strip().upper(),
            'gender': form_data['client_gender'],
            'email': form_data.get('client_email', '').strip().lower(),
            'phone': form_data.get('client_phone', '').strip(),
            'notes': form_data.get('client_notes', '').strip(),
            'is_active': form_data.get('client_is_active', True)
        }
        
        if Client.objects.filter(dni=client_data['dni']).exists():
            raise ValidationError(f"Ya existe un cliente con el DNI {client_data['dni']}")
        
        return Client.objects.create(**client_data)
    
    @staticmethod
    def _create_service_from_data(client, form_data: Dict[str, Any], business_line, category):
        price = form_data.get('price')
        
        if price is None or (isinstance(price, (int, float)) and price <= 0):
            raise ValidationError(f"El precio del servicio es obligatorio y debe ser mayor que 0. Recibido: {price}")
        
        service = ClientService(
            client=client,
            business_line=business_line,
            category=category,
            price=price,
            start_date=form_data.get('start_date'),
            admin_status=form_data.get('admin_status', 'ENABLED'),
            notes=form_data.get('notes', '').strip(),
            remanentes=form_data.get('remanentes', {}),
            is_active=True
        )
        
        service.save()
        return service
