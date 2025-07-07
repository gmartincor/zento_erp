from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, UpdateView
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from apps.core.constants import TENANT_SUCCESS_MESSAGES, TENANT_ERROR_MESSAGES
from apps.core.mixins import TenantContextMixin
from .forms import TenantUpdateForm, TenantStatusForm
from .services import TenantService, TenantDataService
from .models import Tenant


class BaseTenantView(TenantContextMixin):
    model = Tenant
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_tenant_context())
        return context


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
        
        context.update({
            'page_title': f'Nutricionista: {tenant.name}',
            'subtitle': f'Gestión de {tenant.subdomain}',
        })
        return context


@method_decorator(login_required, name='dispatch')
class TenantUpdateView(BaseTenantView, UpdateView):
    form_class = TenantUpdateForm
    template_name = 'tenants/update.html'
    context_object_name = 'tenant'
    success_url = reverse_lazy('admin:tenants_tenant_changelist')
    
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
                
                return redirect('admin:tenants_tenant_changelist')
                
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
