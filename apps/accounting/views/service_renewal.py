from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError

from ..models import ClientService
from ..forms.service_renewal_form import ServiceRenewalForm
from ..services.period_service import ServicePeriodManager


@login_required
@require_http_methods(["GET", "POST"])
def service_renewal_view(request, service_id):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    if request.method == 'POST':
        form = ServiceRenewalForm(client_service=client_service, data=request.POST)
        
        if form.is_valid():
            try:
                period = form.save()
                
                if period.is_period_only:
                    messages.success(
                        request, 
                        f"Servicio extendido exitosamente hasta {client_service.end_date}. "
                        f"Se creó un período pendiente de pago."
                    )
                else:
                    messages.success(
                        request, 
                        f"Servicio extendido y pago procesado exitosamente. "
                        f"Nuevo período: {period.period_start} - {period.period_end}"
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
        form = ServiceRenewalForm(client_service=client_service)
    

    pending_summary = ServicePeriodManager.get_unpaid_periods_summary(client_service)
    
    context = {
        'form': form,
        'client_service': client_service,
        'client': client_service.client,
        'pending_periods_summary': pending_summary,
        'current_end_date': client_service.end_date,
        'can_extend': True
    }
    
    return render(request, 'accounting/service_renewal.html', context)


@login_required
@require_http_methods(["POST"])
def ajax_calculate_extension_dates(request, service_id):
    """
    Vista AJAX para calcular fechas de extensión dinámicamente.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    
    try:
        duration_months = int(request.POST.get('duration_months', 1))
        
        current_end = client_service.end_date
        if current_end is None:
            return JsonResponse({
                'success': False,
                'error': 'No se puede calcular un período para un servicio sin fecha de fin'
            })
        
        from datetime import timedelta
        new_start = current_end + timedelta(days=1)
        new_end = new_start + timedelta(days=duration_months * 30 - 1)
        

        from ..services.payment_service import PaymentService
        from ..models import ServicePayment
        
        temp_period = ServicePayment(
            client_service=client_service,
            period_start=new_start,
            period_end=new_end
        )
        
        suggested_amount = PaymentService.calculate_suggested_amount(temp_period, client_service)
        
        return JsonResponse({
            'success': True,
            'new_start': new_start.isoformat(),
            'new_end': new_end.isoformat(),
            'duration_days': (new_end - new_start).days + 1,
            'suggested_amount': float(suggested_amount) if suggested_amount else None,
            'service_end_date': new_end.isoformat()
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def service_extension_preview(request, service_id):
    """
    Vista para mostrar una preview de la extensión antes de confirmar.
    """
    client_service = get_object_or_404(ClientService, id=service_id)
    
    duration_months = int(request.GET.get('months', 1))
    
    current_end = client_service.end_date
    if current_end is None:
        return JsonResponse({
            'success': False,
            'error': 'No se puede calcular un período para un servicio sin fecha de fin'
        })
    
    from datetime import timedelta
    new_start = current_end + timedelta(days=1)
    new_end = new_start + timedelta(days=duration_months * 30 - 1)
    
    context = {
        'client_service': client_service,
        'extension_details': {
            'current_end': current_end,
            'new_start': new_start,
            'new_end': new_end,
            'duration_months': duration_months,
            'duration_days': (new_end - new_start).days + 1
        }
    }
    
    return render(request, 'accounting/service_extension_preview.html', context)
