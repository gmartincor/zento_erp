from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django import forms
from datetime import date

from ..models import ClientService
from ..services.service_termination_manager import ServiceTerminationManager
from apps.core.mixins import BusinessLineHierarchyMixin


class ServiceTerminationForm(forms.Form):
    termination_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white'
        }),
        label="Fecha de finalización",
        initial=date.today,
        help_text="Fecha en que el servicio se da de baja definitivamente"
    )
    
    reason = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
            'placeholder': 'Motivo de la finalización (opcional)'
        }),
        label="Motivo"
    )


@login_required
@require_http_methods(["GET", "POST"])
def service_termination_view(request, service_id):
    service = get_object_or_404(ClientService, id=service_id)
    
    if not ServiceTerminationManager.can_terminate_service(service):
        messages.error(request, "El servicio ya está inactivo")
        return redirect('accounting:service-edit', 
                       line_path=service.get_line_path(),
                       category=service.category,
                       service_id=service_id)
    
    mixin = BusinessLineHierarchyMixin()
    breadcrumb_path = mixin.get_breadcrumb_path(service.business_line, service.category)
    
    if request.method == 'POST':
        form = ServiceTerminationForm(request.POST)
        
        if form.is_valid():
            try:
                ServiceTerminationManager.terminate_service(
                    service=service,
                    termination_date=form.cleaned_data['termination_date'],
                    reason=form.cleaned_data.get('reason')
                )
                
                messages.success(
                    request,
                    f"Servicio finalizado exitosamente el {form.cleaned_data['termination_date'].strftime('%d/%m/%Y')}"
                )
                
                return redirect('accounting:service-edit', 
                               line_path=service.get_line_path(),
                               category=service.category,
                               service_id=service_id)
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = ServiceTerminationForm()
    
    context = {
        'form': form,
        'service': service,
        'breadcrumb_path': breadcrumb_path,
        'page_title': 'Finalizar Servicio',
        'hide_terminate_button': True
    }
    
    return render(request, 'accounting/service_termination.html', context)


@login_required
@require_http_methods(["POST"])
def service_reactivation_view(request, service_id):
    service = get_object_or_404(ClientService, id=service_id)
    
    if not ServiceTerminationManager.can_reactivate_service(service):
        messages.error(request, "El servicio no puede ser reactivado")
    else:
        try:
            ServiceTerminationManager.reactivate_service(service)
            messages.success(request, "Servicio reactivado exitosamente")
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error inesperado: {str(e)}")
    
    return redirect('accounting:service-edit', 
                   line_path=service.get_line_path(),
                   category=service.category,
                   service_id=service_id)
