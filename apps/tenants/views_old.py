from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.core.constants import TENANT_SUCCESS_MESSAGES, TENANT_ERROR_MESSAGES
from apps.core.mixins import TenantContextMixin
from .forms import TenantRegistrationForm, TenantUpdateForm, TenantStatusForm
from .services import TenantService, TenantDataService
from .models import Tenant


class BaseTenantView(TenantContextMixin):
    model = Tenant
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_tenant_context())
        return context


@require_http_methods(["GET", "POST"])
def tenant_registration_view(request):
    if request.method == 'POST':
        form = TenantRegistrationForm(request.POST)
        
        if form.is_valid():
            try:
                tenant, domain = TenantService.create_tenant(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    subdomain=form.cleaned_data['subdomain']
                )
                
                try:
                    TenantDataService.create_sample_data_for_tenant(tenant)
                except Exception:
                    pass
                
                messages.success(
                    request,
                    TENANT_SUCCESS_MESSAGES['TENANT_CREATED'].format(name=tenant.name)
                )
                
                return redirect('tenants:success')
                
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error inesperado: {str(e)}")
    else:
        form = TenantRegistrationForm()
    
    context = {
        'form': form,
        'page_title': 'Registro de Nutricionista',
        'subtitle': 'Crea tu cuenta profesional en el sistema',
    }
    
    return render(request, 'tenants/register.html', context)


@require_http_methods(["GET"])
def tenant_success_view(request):
    context = {
        'page_title': 'Registro Exitoso',
        'subtitle': 'Tu cuenta ha sido creada correctamente',
        'message': 'Pronto recibirás un email con las instrucciones de activación.',
    }
    
    return render(request, 'tenants/success.html', context)


@require_http_methods(["GET"])
def tenant_testing_view(request):
    from .testing import TenantTestingService
    
    try:
        isolation_results = TenantTestingService.verify_isolation()
        context = {
            'page_title': 'Testing de Aislamiento',
            'subtitle': 'Verificación de separación de datos entre tenants',
            'results': isolation_results,
            'success': True,
        }
    except Exception as e:
        context = {
            'page_title': 'Testing de Aislamiento',
            'subtitle': 'Error en la verificación',
            'error': str(e),
            'success': False,
        }
    
    return render(request, 'tenants/testing.html', context)


@method_decorator(login_required, name='dispatch')
class TenantListView(BaseTenantView, ListView):
    template_name = 'tenants/list.html'
    context_object_name = 'tenants'
    paginate_by = 25
    
    def get_queryset(self):
        return Tenant.active_objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Nutricionistas Registrados',
            'subtitle': 'Gestión de cuentas profesionales',
            'stats': {
                'total': Tenant.objects.count(),
                'active': Tenant.active_objects.count(),
                'pending': Tenant.objects.pending().count(),
                'suspended': Tenant.objects.suspended().count(),
            }
        })
        return context


@method_decorator(login_required, name='dispatch')
class TenantDetailView(BaseTenantView, DetailView):
    template_name = 'tenants/detail.html'
    context_object_name = 'tenant'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_object()
        
        try:
            def get_tenant_stats():
                from apps.accounting.models import Client
                from apps.business_lines.models import BusinessLine
                
                return {
                    'clients_count': Client.objects.count(),
                    'business_lines_count': BusinessLine.objects.count(),
                }
            
            stats = TenantDataService.execute_in_tenant_context(
                tenant, get_tenant_stats
            ) if tenant.is_available else {}
            
        except Exception:
            stats = {}
        
        context.update({
            'page_title': f'Nutricionista: {tenant.name}',
            'subtitle': f'Gestión de {tenant.subdomain}',
            'tenant_stats': stats,
        })
        return context


@method_decorator(login_required, name='dispatch')
class TenantUpdateView(BaseTenantView, UpdateView):
    form_class = TenantUpdateForm
    template_name = 'tenants/update.html'
    context_object_name = 'tenant'
    success_url = reverse_lazy('tenants:list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            TENANT_SUCCESS_MESSAGES['TENANT_UPDATED'].format(name=self.object.name)
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': f'Editar: {self.object.name}',
            'subtitle': 'Actualizar información del nutricionista',
        })
        return context


@login_required
@require_http_methods(["GET", "POST"])
def tenant_status_update_view(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    
    if request.method == 'POST':
        form = TenantStatusForm(request.POST, instance=tenant)
        
        if form.is_valid():
            try:
                old_status = tenant.status
                form.save()
                
                if tenant.status == Tenant.StatusChoices.ACTIVE and old_status != Tenant.StatusChoices.ACTIVE:
                    tenant.activate()
                elif tenant.status == Tenant.StatusChoices.SUSPENDED:
                    TenantService.suspend_tenant(tenant.id, form.cleaned_data.get('notes'))
                
                messages.success(
                    request,
                    f"Estado de {tenant.name} actualizado a {tenant.get_status_display()}"
                )
                
                return redirect('tenants:detail', pk=tenant.pk)
                
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        form = TenantStatusForm(instance=tenant)
    
    context = {
        'form': form,
        'tenant': tenant,
        'page_title': f'Cambiar Estado: {tenant.name}',
        'subtitle': 'Gestión de estado del nutricionista',
    }
    
    return render(request, 'tenants/status_update.html', context)
