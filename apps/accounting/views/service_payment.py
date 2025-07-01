from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import ClientService, ServicePayment
from ..forms.service_payment_form import PaymentForm
from ..services.payment_service import PaymentService
from ..services.period_service import ServicePeriodManager


@login_required
@require_http_methods(["GET", "POST"])
def service_payment_view(request, service_id):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    if request.method == 'POST':
        form = PaymentForm(client_service=client_service, data=request.POST)
        
        if form.is_valid():
            try:
                # El método save() ahora maneja tanto pagos como remanentes
                updated_periods = form.save(user=request.user)
                
                success_msg = f"Procesados {len(updated_periods)} pagos exitosamente."
                
                messages.success(request, success_msg)
                
                return redirect('accounting:client-service-detail', service_id=service_id)
                
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
        form = PaymentForm(client_service=client_service)
    

    pending_summary = ServicePeriodManager.get_unpaid_periods_summary(client_service)
    payment_history = PaymentService.get_payment_history(client_service)
    
    context = {
        'form': form,
        'client_service': client_service,
        'client': client_service.client,
        'pending_periods': pending_summary.get('periods', []),
        'pending_periods_summary': pending_summary,
        'payment_history': payment_history[:5],
        'has_pending_periods': pending_summary['count'] > 0,
        'today': timezone.now().date()
    }
    
    return render(request, 'accounting/service_payment_v2.html', context)


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
        period.save()
        
        messages.success(
            request,
            f"Período {period.period_start} - {period.period_end} cancelado exitosamente"
        )
        
    except Exception as e:
        messages.error(request, f"Error al cancelar período: {str(e)}")
    
    return redirect('accounting:client_service_detail', service_id=service_id)
