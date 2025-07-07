from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    if request.user.is_authenticated:
        user_tenant = get_user_tenant(request.user)
        if user_tenant:
            return redirect('tenant_dashboard', tenant_slug=user_tenant.slug)
        else:
            messages.error(request, 'Usuario sin tenant asignado')
            return redirect('unified_login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                user_tenant = get_user_tenant(user)
                if user_tenant:
                    login(request, user)
                    messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
                    return redirect('tenant_dashboard', tenant_slug=user_tenant.slug)
                else:
                    messages.error(request, 'Usuario sin tenant asignado')
            else:
                messages.error(request, 'Credenciales inválidas')
        else:
            messages.error(request, 'Por favor, completa todos los campos')
    
    context = {
        'page_title': 'Acceso - Nutrition Pro CRM',
        'show_unified_branding': True,
    }
    
    return render(request, 'authentication/unified_login.html', context)


def get_user_tenant(user):
    if hasattr(user, 'profile') and user.profile:
        return user.profile.tenant
    
    tenants = Tenant.objects.filter(is_active=True, is_deleted=False)
    
    user_tenant_mapping = {
        'carlos.glow': 'carlos',
        'maria.glow': 'maria', 
        'ana.martinez': 'ana-martinez',
        'admin': 'admin'
    }
    
    if user.username in user_tenant_mapping:
        tenant_slug = user_tenant_mapping[user.username]
        try:
            return tenants.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            pass
    
    for tenant in tenants:
        if user.username.startswith(tenant.slug.replace('-', '.')):
            return tenant
    
    return None
