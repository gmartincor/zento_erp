from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.utils.safestring import mark_safe
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
        initial=date.today
    )
    
    reason = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white',
            'placeholder': 'Ej: Cliente solicitó pausa, cambio de plan, finalización natural...'
        }),
        label="Motivo de finalización",
        help_text="Opcional: Anota el motivo para futuras referencias"
    )
    
    def __init__(self, service=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = service
        
        if service:
            from ..services.service_termination_manager import ServiceTerminationManager
            limits = ServiceTerminationManager.get_termination_date_limits(service)
            
            if limits['max_date']:
                self.fields['termination_date'].widget.attrs['max'] = limits['max_date'].isoformat()
            
            if limits['min_date']:
                self.fields['termination_date'].widget.attrs['min'] = limits['min_date'].isoformat()
    
    def clean_termination_date(self):
        termination_date = self.cleaned_data['termination_date']
        
        if self.service:
            from ..services.service_termination_manager import ServiceTerminationManager
            limits = ServiceTerminationManager.get_termination_date_limits(self.service)
            
            if limits['max_date'] and termination_date > limits['max_date']:
                max_date_str = limits['max_date'].strftime('%d/%m/%Y')
                from django.utils.safestring import mark_safe
                raise forms.ValidationError(
                    mark_safe(
                        f"La fecha máxima de finalización es el {max_date_str} (último período creado). "
                        f"Para extender más allá de esta fecha, primero "
                        f"<a href='/accounting/services/{self.service.id}/renewal/' class='text-blue-600 hover:text-blue-800 underline'>crea un nuevo período</a>."
                    )
                )
            
            if limits['min_date'] and termination_date < limits['min_date']:
                min_date_str = limits['min_date'].strftime('%d/%m/%Y')
                raise forms.ValidationError(
                    f"La fecha mínima de finalización es el {min_date_str} (inicio del servicio)."
                )
        
        return termination_date


@login_required
@require_http_methods(["GET", "POST"])
def service_termination_view(request, service_id):
    service = get_object_or_404(ClientService, id=service_id)
    
    if not ServiceTerminationManager.can_terminate_service(service):
        messages.error(request, "El servicio ya está inactivo")
        return redirect('accounting:category-services', 
                       line_path=service.get_line_path(),
                       category=service.category) + '?view=grid'
    
    mixin = BusinessLineHierarchyMixin()
    breadcrumb_path = mixin.get_breadcrumb_path(service.business_line, service.category)
    
    if request.method == 'POST':
        form = ServiceTerminationForm(service, request.POST)
        
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
                
                return redirect('accounting:category-services', 
                               line_path=service.get_line_path(),
                               category=service.category) + '?view=grid'
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = ServiceTerminationForm(service)
    
    context = {
        'form': form,
        'service': service,
        'breadcrumb_path': breadcrumb_path,
        'page_title': 'Finalizar Servicio',
        'hide_terminate_button': True
    }
    
    return render(request, 'accounting/service_termination.html', context)
