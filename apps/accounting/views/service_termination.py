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
        help_text="Último día en que el servicio estará activo"
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
                max_date_str = limits['max_date'].strftime('%d/%m/%Y')
                self.fields['termination_date'].help_text = (
                    f"Puedes finalizar el servicio hasta el {max_date_str} (último período creado). "
                    f"Para extender más allá de esta fecha, primero crea un nuevo período desde 'Renovar Servicio'."
                )
                self.fields['termination_date'].widget.attrs['max'] = limits['max_date'].isoformat()
            else:
                self.fields['termination_date'].help_text = (
                    "Este servicio no tiene períodos definidos. "
                    "Puedes finalizar en cualquier fecha o crear períodos desde 'Renovar Servicio'."
                )
            
            if limits['min_date']:
                min_date_str = limits['min_date'].strftime('%d/%m/%Y')
                current_help = self.fields['termination_date'].help_text
                self.fields['termination_date'].help_text = (
                    f"La fecha mínima de finalización es {min_date_str} (inicio del servicio). "
                    f"{current_help}"
                )
                self.fields['termination_date'].widget.attrs['min'] = limits['min_date'].isoformat()
    
    def clean_termination_date(self):
        termination_date = self.cleaned_data['termination_date']
        
        if self.service:
            from ..services.service_termination_manager import ServiceTerminationManager
            try:
                ServiceTerminationManager.validate_termination_date(self.service, termination_date)
            except ValidationError as e:
                raise forms.ValidationError(str(e))
        
        return termination_date


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
                
                return redirect('accounting:service-edit', 
                               line_path=service.get_line_path(),
                               category=service.category,
                               service_id=service_id)
                
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
