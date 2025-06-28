from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from ..models import ClientService, ServicePayment
from ..forms.service_payment_form import ServicePaymentForm, BulkPaymentForm
from ..services.payment_service import PaymentService
from ..services.period_service import ServicePeriodManager


@login_required
@require_http_methods(["GET", "POST"])
def service_payment_view(request, service_id):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    if request.method == 'POST':
        form = ServicePaymentForm(client_service=client_service, data=request.POST)
        
        if form.is_valid():
            try:
                updated_period = form.save()
                
                messages.success(
                    request,
                    f"Pago procesado exitosamente. "
                    f"Período {updated_period.period_start} - {updated_period.period_end} "
                    f"marcado como pagado por {updated_period.amount}€"
                )
                
                return redirect('accounting:client_service_detail', service_id=service_id)
                
            except ValidationError as e:
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"{field}: {error}")
                else:
                    messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = ServicePaymentForm(client_service=client_service)
    

    pending_summary = ServicePeriodManager.get_unpaid_periods_summary(client_service)
    payment_history = PaymentService.get_payment_history(client_service)
    
    context = {
        'form': form,
        'client_service': client_service,
        'client': client_service.client,
        'pending_periods_summary': pending_summary,
        'payment_history': payment_history[:5],
        'has_pending_periods': pending_summary['count'] > 0
    }
    
    return render(request, 'accounting/service_payment_v2.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def bulk_payment_view(request, service_id):
    """
    Vista para procesar múltiples pagos de forma masiva.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    
    if request.method == 'POST':
        form = BulkPaymentForm(client_service=client_service, data=request.POST)
        
        if form.is_valid():
            try:
                updated_periods = form.save()
                
                messages.success(
                    request,
                    f"Procesados {len(updated_periods)} pagos exitosamente. "
                    f"Total de períodos actualizados: {len(updated_periods)}"
                )
                
                return redirect('accounting:client_service_detail', service_id=service_id)
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = BulkPaymentForm(client_service=client_service)
    
    pending_summary = ServicePeriodManager.get_unpaid_periods_summary(client_service)
    
    context = {
        'form': form,
        'client_service': client_service,
        'client': client_service.client,
        'pending_periods_summary': pending_summary
    }
    
    return render(request, 'accounting/bulk_payment.html', context)


@login_required
@require_http_methods(["POST"])
def ajax_get_suggested_amount(request, service_id, period_id):
    """
    Vista AJAX para obtener monto sugerido para un período específico.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    period = get_object_or_404(ServicePayment, id=period_id, client_service=client_service)
    
    try:
        suggested_amount = PaymentService.calculate_suggested_amount(period, client_service)
        
        return JsonResponse({
            'success': True,
            'suggested_amount': float(suggested_amount) if suggested_amount else None,
            'period_info': {
                'start': period.period_start.isoformat(),
                'end': period.period_end.isoformat(),
                'duration_days': period.duration_days,
                'status': period.status
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def payment_options_view(request, service_id):
    """
    Vista para mostrar opciones de pago disponibles.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    
    payment_options = PaymentService.get_payment_options_for_service(client_service)
    pending_summary = ServicePeriodManager.get_unpaid_periods_summary(client_service)
    
    context = {
        'client_service': client_service,
        'client': client_service.client,
        'payment_options': payment_options,
        'pending_summary': pending_summary
    }
    
    return render(request, 'accounting/payment_options.html', context)


@login_required
@require_http_methods(["GET"])
def service_payment_history_view(request, service_id):
    """
    Vista para mostrar el historial completo de pagos de un servicio específico.
    """
    from apps.accounting.services.history_service import HistoryService
    
    client_service = get_object_or_404(ClientService, id=service_id)
    payment_history = HistoryService.get_service_payment_history(service_id)
    
    context = {
        'service': client_service,
        'client': client_service.client,
        'payments': payment_history,
        'stats': HistoryService.get_history_summary(service_id=service_id)
    }
    
    return render(request, 'accounting/payments/service_history.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_period_view(request, service_id, period_id):
    """
    Vista para cancelar un período pendiente.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    period = get_object_or_404(
        ServicePayment, 
        id=period_id, 
        client_service=client_service,
        status__in=[
            ServicePayment.StatusChoices.PERIOD_CREATED,
            ServicePayment.StatusChoices.PENDING
        ]
    )
    
    try:
        period.status = ServicePayment.StatusChoices.CANCELLED
        period.save(update_fields=['status', 'modified'])
        

        last_active_period = client_service.payments.filter(
            status__in=[
                ServicePayment.StatusChoices.PAID,
                ServicePayment.StatusChoices.PERIOD_CREATED,
                ServicePayment.StatusChoices.PENDING
            ]
        ).exclude(id=period.id).order_by('-period_end').first()
        
        if last_active_period:
            client_service.end_date = last_active_period.period_end
        else:

            pass
        
        client_service.save(update_fields=['end_date', 'modified'])
        
        messages.success(
            request,
            f"Período {period.period_start} - {period.period_end} cancelado exitosamente"
        )
        
    except Exception as e:
        messages.error(request, f"Error al cancelar período: {str(e)}")
    
    return redirect('accounting:client_service_detail', service_id=service_id)
