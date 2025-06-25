from typing import Dict, Any, Tuple
from django.db import transaction
from django.urls import reverse

from apps.accounting.models import ClientService
from apps.accounting.services.client_service_transaction import ClientServiceTransactionManager
from apps.accounting.services.service_history_manager import ServiceHistoryManager


class ServiceRenewalManager:
    
    @staticmethod
    @transaction.atomic
    def create_renewal_service(
        original_service: ClientService,
        new_service_data: Dict[str, Any]
    ) -> Tuple[ClientService, str]:
        
        renewal_data = ServiceRenewalManager._prepare_renewal_data(
            original_service, new_service_data
        )
        
        new_service = ClientServiceTransactionManager.create_client_service(
            renewal_data,
            original_service.business_line,
            original_service.category
        )
        
        redirect_url = reverse('accounting:payment-create', kwargs={'service_id': new_service.id})
        return new_service, redirect_url
    
    @staticmethod
    def _prepare_renewal_data(
        original_service: ClientService,
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        
        client = original_service.client
        
        return {
            'client_name': client.full_name,
            'client_dni': client.dni,
            'client_gender': client.gender,
            'client_email': client.email,
            'client_phone': client.phone,
            'client_notes': client.notes,
            'price': new_data.get('price', original_service.price),
            'notes': new_data.get('notes', ''),
            'remanentes': new_data.get('remanentes', original_service.remanentes),
            **{k: v for k, v in new_data.items() 
               if k not in ['client_name', 'client_dni', 'client_gender', 
                           'client_email', 'client_phone', 'client_notes']}
        }
    
    @staticmethod
    def get_renewal_suggestions(original_service: ClientService) -> Dict[str, Any]:
        latest_payment = original_service.payments.filter(
            status='PAID'
        ).order_by('-period_end').first()
        
        return {
            'suggested_price': original_service.price,
            'last_payment_date': latest_payment.payment_date if latest_payment else None,
            'last_period_end': latest_payment.period_end if latest_payment else None,
            'service_count': ServiceHistoryManager.get_client_service_history(
                original_service.client,
                original_service.business_line,
                original_service.category
            ).count() + 1
        }
