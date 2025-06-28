from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.urls import reverse

from ..models import ClientService
from ..forms.service_renewal_form import ServiceRenewalForm
from ..services.period_service import ServicePeriodManager
from apps.core.mixins import BusinessLineHierarchyMixin


@login_required
@require_http_methods(["GET", "POST"])
def service_renewal_view(request, service_id):
    client_service = get_object_or_404(ClientService, id=service_id)
    
    # Crear una instancia del mixin para obtener el breadcrumb
    mixin = BusinessLineHierarchyMixin()
    breadcrumb_path = mixin.get_breadcrumb_path(
        client_service.business_line, 
        client_service.category
    )
    
    if request.method == 'POST':
        form = ServiceRenewalForm(client_service=client_service, data=request.POST)
        
        if form.is_valid():
            try:
                period = form.save()
                
                if period.is_period_only:
                    action = "activado" if not client_service.end_date else "extendido"
                    messages.success(
                        request, 
                        f"Servicio {action} exitosamente hasta {period.period_end}. "
                        f"Se creó un período pendiente de pago."
                    )
                else:
                    action = "activado" if not client_service.end_date else "extendido"
                    messages.success(
                        request, 
                        f"Servicio {action} y pago procesado exitosamente. "
                        f"Nuevo período: {period.period_start} - {period.period_end}"
                    )
                
                return redirect('accounting:service-edit', 
                              line_path=client_service.get_line_path(),
                              category=client_service.category,
                              service_id=service_id)
                
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
        'breadcrumb_path': breadcrumb_path,
        'pending_periods_summary': pending_summary,
        'current_end_date': client_service.end_date,
        'can_extend': True
    }
    
    return render(request, 'accounting/service_renewal.html', context)
