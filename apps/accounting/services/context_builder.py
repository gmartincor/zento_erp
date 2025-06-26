from typing import Dict, Any, Optional
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse

from ..models import ClientService, ServicePayment
from .service_state_manager import ServiceStateManager
from .payment_service import PaymentService


class RenewalContextBuilder:
    
    def __init__(self, service: ClientService):
        self.service = service
        self._cache = {}
    
    def build_form_context(self) -> Dict[str, Any]:
        if 'form_context' not in self._cache:
            options = self._get_renewal_options()
            
            self._cache['form_context'] = {
                'default_amount': self.service.price,
                'suggested_start_date': options['suggested_start_date'],
                'default_payment_method': options['last_payment_method'],
                'available_actions': self._get_available_actions(options),
                'validation_requirements': self._get_validation_requirements(options)
            }
        
        return self._cache['form_context']
    
    def build_view_context(self, back_url_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if 'view_context' not in self._cache:
            options = self._get_renewal_options()
            status_data = ServiceStateManager.get_status_display_data(self.service)
            
            self._cache['view_context'] = {
                'service': self.service,
                'options': options,
                'status_data': status_data,
                'page_title': f'Gestionar Servicio - {self.service.client.full_name}',
                'back_url': self._build_back_url(back_url_kwargs),
                'display_info': self._build_display_info(options, status_data)
            }
        
        return self._cache['view_context']
    
    def build_complete_context(self, back_url_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        form_context = self.build_form_context()
        view_context = self.build_view_context(back_url_kwargs)
        
        return {
            **form_context,
            **view_context,
            'context_meta': {
                'builder_version': '1.0',
                'generated_at': timezone.now(),
                'service_id': self.service.id
            }
        }
    
    def get_action_defaults(self, action_type: str) -> Dict[str, Any]:
        options = self._get_renewal_options()
        
        defaults = {
            'amount': self.service.price,
            'duration_months': 1,
            'payment_date': timezone.now().date(),
            'payment_method': options['last_payment_method']
        }
        
        if action_type == 'renew':
            defaults['start_date'] = options['suggested_start_date']
        elif action_type == 'extend':
            defaults.pop('start_date', None)
        elif action_type == 'no_renew':
            return {'no_renew_reason': ''}
        
        return defaults
    
    def _get_renewal_options(self) -> Dict[str, Any]:
        if 'renewal_options' not in self._cache:
            status_data = ServiceStateManager.get_status_display_data(self.service)
            active_until = PaymentService.get_service_active_until(self.service)
            
            self._cache['renewal_options'] = {
                'can_extend': status_data['status'] == 'ACTIVE',
                'can_renew': status_data['status'] in ['ACTIVE', 'EXPIRED'],
                'needs_renewal': status_data['needs_renewal'],
                'is_expired': status_data['status'] == 'EXPIRED',
                'current_active_until': active_until,
                'suggested_start_date': self._calculate_suggested_start_date(active_until),
                'suggested_amount': self.service.price,
                'last_payment_method': PaymentService.get_service_current_payment_method(self.service)
            }
        
        return self._cache['renewal_options']
    
    def _calculate_suggested_start_date(self, active_until: Optional[date]) -> date:
        if active_until:
            if active_until >= timezone.now().date():
                return active_until + timedelta(days=1)
            else:
                return timezone.now().date()
        else:
            return timezone.now().date()
    
    def _get_available_actions(self, options: Dict[str, Any]) -> list:
        actions = []
        
        if options['can_extend']:
            actions.append(('extend', 'Extender servicio actual'))
        
        if options['can_renew']:
            actions.append(('renew', 'Crear nuevo servicio (renovación)'))
        
        actions.append(('no_renew', 'Marcar como no renovado'))
        
        return actions
    
    def _get_validation_requirements(self, options: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'extend_requires_payment': True,
            'renew_requires_start_date': True,
            'amount_required_for_extend_renew': True,
            'payment_method_required_when_payment_now': True
        }
    
    def _build_back_url(self, back_url_kwargs: Optional[Dict[str, Any]] = None) -> str:
        if back_url_kwargs:
            return reverse('accounting:category-services', kwargs=back_url_kwargs)
        
        return reverse('accounting:category-services', kwargs={
            'line_path': self.service.get_line_path(),
            'category': self.service.category
        })
    
    def _build_display_info(self, options: Dict[str, Any], status_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'client_name': self.service.client.full_name,
            'business_line_name': self.service.business_line.name,
            'category_display': self.service.get_category_display(),
            'current_price': self.service.price,
            'status_badge_data': status_data,
            'needs_attention': options['needs_renewal'] or options['is_expired'],
            'attention_message': self._get_attention_message(options)
        }
    
    def _get_attention_message(self, options: Dict[str, Any]) -> Optional[str]:
        if options['is_expired']:
            return "Este servicio ha expirado y necesita renovación."
        elif options['needs_renewal']:
            return "Este servicio necesita gestión."
        return None


class RenewalFormContextMixin:
    
    def __init__(self, *args, service=None, **kwargs):
        super().__init__(*args, **kwargs)
        if service:
            self.service = service
            self.context_builder = RenewalContextBuilder(service)
            self._apply_form_context()
    
    def _apply_form_context(self):
        context = self.context_builder.build_form_context()
        
        if 'amount' in self.fields and context['default_amount']:
            self.fields['amount'].initial = context['default_amount']
        
        if 'start_date' in self.fields and context['suggested_start_date']:
            self.fields['start_date'].initial = context['suggested_start_date']
        
        if 'payment_method' in self.fields and context['default_payment_method']:
            self.fields['payment_method'].initial = context['default_payment_method']
        
        if 'action_type' in self.fields:
            self.fields['action_type'].choices = context['available_actions']


class RenewalViewContextMixin:
    
    def get_renewal_context_data(self, **kwargs):
        if not hasattr(self, 'service'):
            raise ValueError("View must have a 'service' attribute to use RenewalViewContextMixin")
        
        context_builder = RenewalContextBuilder(self.service)
        
        back_url_kwargs = None
        if hasattr(self, 'get_back_url_kwargs'):
            back_url_kwargs = self.get_back_url_kwargs()
        
        return context_builder.build_view_context(back_url_kwargs)
