from typing import Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounting.models import Client, ClientService
from apps.accounting.services.payment_service import PaymentService


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
            
            payment_validation = PaymentService.validate_payment_consistency_after_service_update(service_instance)
            if payment_validation['warnings'] or payment_validation['recommendations']:
                service_instance._payment_validation_info = payment_validation
            
            return service_instance
            
        except Exception as e:
            raise ValidationError(f"Error al actualizar cliente y servicio: {str(e)}")
    
    @staticmethod
    @transaction.atomic
    def create_client_service(form_data: Dict[str, Any], business_line, category) -> ClientService:
        try:
            client = ClientServiceTransactionManager._create_client_from_data(form_data)
            service = ClientServiceTransactionManager._create_service_from_data(
                client, form_data, business_line, category
            )
            
            return service
            
        except Exception as e:
            raise ValidationError(f"Error al crear cliente y servicio: {str(e)}")
    
    @staticmethod
    def _update_client_data(client: Client, form_data: Dict[str, Any]) -> None:
        client.full_name = form_data.get('client_name', client.full_name).strip().title()
        client.dni = form_data.get('client_dni', client.dni).strip().upper()
        client.gender = form_data.get('client_gender', client.gender)
        client.email = form_data.get('client_email', client.email or '').strip().lower()
        client.phone = form_data.get('client_phone', client.phone or '').strip()
        client.notes = form_data.get('client_notes', client.notes or '').strip()
        
        if Client.objects.filter(dni=client.dni).exclude(pk=client.pk).exists():
            raise ValidationError(f"Ya existe otro cliente con el DNI {client.dni}")
    
    @staticmethod
    def _update_service_data(service, form_data: Dict[str, Any]) -> None:
        service.price = form_data.get('price', service.price)
        service.start_date = form_data.get('start_date', service.start_date)
        service.end_date = form_data.get('end_date', service.end_date)
        service.admin_status = form_data.get('admin_status', service.admin_status)
        service.notes = form_data.get('notes', service.notes or '').strip()
        
        if 'remanentes' in form_data:
            service.remanentes = form_data['remanentes']
        
        if service.category == 'BLACK' and service.business_line.has_remanente:
            if not service.business_line.remanente_field:
                raise ValidationError(
                    f'La línea de negocio {service.business_line.name} no tiene configurado el tipo de remanente.'
                )
    
    @staticmethod
    def _create_client_from_data(form_data: Dict[str, Any]) -> Client:
        client = Client(
            full_name=form_data['client_name'].strip().title(),
            dni=form_data['client_dni'].strip().upper(),
            gender=form_data['client_gender'],
            email=form_data.get('client_email', '').strip().lower(),
            phone=form_data.get('client_phone', '').strip(),
            notes=form_data.get('client_notes', '').strip(),
            is_active=True
        )
        
        if Client.objects.filter(dni=client.dni).exists():
            raise ValidationError(f"Ya existe un cliente con el DNI {client.dni}")
        
        client.save()
        return client
    
    @staticmethod
    def _create_service_from_data(client, form_data: Dict[str, Any], business_line, category):
        service = ClientService(
            client=client,
            business_line=business_line,
            category=category,
            price=form_data.get('price', 0.00),
            start_date=form_data.get('start_date'),
            end_date=form_data.get('end_date'),
            admin_status=form_data.get('admin_status', 'ENABLED'),
            notes=form_data.get('notes', '').strip(),
            remanentes=form_data.get('remanentes', {}),
            is_active=True
        )
        
        service.save()
        return service
