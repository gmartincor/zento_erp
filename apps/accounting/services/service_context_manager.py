from typing import Dict, Any, Optional
from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.urls import reverse

from apps.accounting.models import ClientService
from apps.accounting.services.service_history_manager import ServiceHistoryManager
from apps.accounting.services.payment_service import PaymentService


class ServiceContextManager:
    
    @staticmethod
    def build_service_context(service: ClientService) -> Dict[str, Any]:
        return {
            'service': service,
            'client': service.client,
            'business_line': service.business_line,
            'category': service.category,
            'category_display': service.get_category_display(),
        }
    
    @staticmethod
    def build_service_history_context(service: ClientService) -> Dict[str, Any]:
        base_context = ServiceContextManager.build_service_context(service)
        
        history = ServiceHistoryManager.get_client_service_history(
            service.client, service.business_line, service.category
        )
        
        statistics = ServiceHistoryManager.get_service_statistics(
            service.client, service.business_line, service.category
        )
        
        base_context.update({
            'service_history': history,
            'history_statistics': statistics,
            'is_latest_service': history.first() == service if history.exists() else True,
        })
        
        return base_context
    
    @staticmethod
    def build_payment_context(service: ClientService) -> Dict[str, Any]:
        base_context = ServiceContextManager.build_service_context(service)
        
        payment = service.payments.first()
        if payment:
            base_context.update({
                'payment': payment,
                'payment_status': payment.payment_status_detailed,
                'days_until_due': payment.days_until_due,
                'was_paid_on_time': payment.was_paid_on_time,
                'days_paid_late': payment.days_paid_late,
            })
        
        base_context.update({
            'has_payment': payment is not None,
            'payment_create_url': reverse('accounting:payment-create', kwargs={'service_id': service.id}),
        })
        
        return base_context
    
    @staticmethod
    def build_renewal_context(service: ClientService) -> Dict[str, Any]:
        base_context = ServiceContextManager.build_service_history_context(service)
        
        from apps.accounting.services.service_renewal_manager import ServiceRenewalManager
        renewal_suggestions = ServiceRenewalManager.get_renewal_suggestions(service)
        
        base_context.update({
            'renewal_suggestions': renewal_suggestions,
            'can_renew': True,
            'renewal_create_url': reverse('accounting:service-create', kwargs={
                'line_path': service.get_line_path(),
                'category': service.category.lower()
            }) + f'?renew_from={service.id}',
        })
        
        return base_context
    
    @staticmethod
    def build_navigation_context(service: ClientService) -> Dict[str, Any]:
        line_path = service.get_line_path()
        category = service.category.lower()
        
        return {
            'back_url': reverse('accounting:category-services', kwargs={
                'line_path': line_path, 
                'category': category
            }),
            'edit_url': reverse('accounting:service-edit', kwargs={
                'line_path': line_path,
                'category': category,
                'service_id': service.id
            }),
            'line_path': line_path,
            'breadcrumb_data': {
                'business_line': service.business_line,
                'category': service.category,
                'client': service.client,
            }
        }
    
    @staticmethod
    def get_service_creation_context(business_line, category):
        return {
            'business_line': business_line,
            'category': category,
            'category_display': 'White' if category == 'WHITE' else 'Black',
        }
    
    @staticmethod
    def get_service_edit_context(service):
        context = ServiceContextManager.build_service_context(service)
        context.update(ServiceContextManager.build_navigation_context(service))
        return context
        
    @staticmethod
    def get_client_history_context(client, services, accessible_lines, request):
        business_lines = accessible_lines.filter(
            id__in=services.values_list('business_line_id', flat=True).distinct()
        )
        
        summary_stats = services.aggregate(
            total_services=Count('id'),
            total_revenue=Sum('payments__amount'),
            white_services=Count('id', filter=Q(category='WHITE')),
            black_services=Count('id', filter=Q(category='BLACK')),
            white_revenue=Sum('payments__amount', filter=Q(category='WHITE')),
            black_revenue=Sum('payments__amount', filter=Q(category='BLACK'))
        )
        
        business_line_breakdown = []
        for line in business_lines:
            line_services = services.filter(business_line=line)
            line_stats = line_services.aggregate(
                count=Count('id'),
                revenue=Sum('payments__amount')
            )
            business_line_breakdown.append({
                'business_line': line,
                'count': line_stats['count'] or 0,
                'revenue': line_stats['revenue'] or Decimal('0'),
                'services': line_services.order_by('-created')[:5]
            })
        
        category_breakdown = [
            {
                'category': 'WHITE',
                'category_display': 'White',
                'count': summary_stats['white_services'] or 0,
                'revenue': summary_stats['white_revenue'] or Decimal('0'),
                'services': services.filter(category='WHITE').order_by('-created')[:5]
            },
            {
                'category': 'BLACK', 
                'category_display': 'Black',
                'count': summary_stats['black_services'] or 0,
                'revenue': summary_stats['black_revenue'] or Decimal('0'),
                'services': services.filter(category='BLACK').order_by('-created')[:5]
            }
        ]
        
        filter_params = {
            'business_line': request.GET.get('business_line', ''),
            'category': request.GET.get('category', ''),
        }
        
        return {
            'summary_stats': summary_stats,
            'business_line_breakdown': business_line_breakdown,
            'category_breakdown': category_breakdown,
            'available_business_lines': business_lines,
            'filter_params': filter_params,
            'total_revenue': summary_stats['total_revenue'] or Decimal('0'),
            'total_services': summary_stats['total_services'] or 0,
        }
    
    @staticmethod
    def get_service_detail_context(service, request):
        from apps.accounting.services.service_renewal_manager import ServiceRenewalManager
        
        payment_summary = service.payments.aggregate(
            total_paid=Sum('amount'),
            payment_count=Count('id')
        )
        
        renewal_info = ServiceRenewalManager.get_renewal_info(service)
        
        related_services = ServiceHistoryManager.get_related_services(
            client=service.client,
            business_line=service.business_line,
            category=service.category,
            exclude_service=service
        )
        
        payment_analysis = {
            'is_paid': service.has_payments,
            'total_paid': payment_summary['total_paid'] or Decimal('0'),
            'payment_count': payment_summary['payment_count'] or 0,
            'compliance_status': service.get_payment_compliance_status(),
            'days_until_due': service.get_days_until_payment_due(),
        }
        
        return {
            'payment_summary': payment_summary,
            'payment_analysis': payment_analysis,
            'renewal_info': renewal_info,
            'related_services': related_services,
            'can_renew': renewal_info['can_renew'],
            'next_payment_date': service.get_next_payment_date(),
        }
