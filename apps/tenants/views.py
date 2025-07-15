from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_tenants.utils import connection
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    current_tenant = connection.tenant
    
    if current_tenant.schema_name == 'public':
        return render(request, 'tenants/public_info.html', {
            'page_title': 'Nutrition Pro CRM - Sistema de Gestión',
        })
    
    if request.user.is_authenticated:
        return _handle_authenticated_user(request, current_tenant)
    
    if request.method == 'POST':
        return _process_login(request, current_tenant)
    
    return render(request, 'authentication/tenant_login.html', {
        'page_title': f'Acceso - {current_tenant.name}',
        'tenant': current_tenant,
    })


@login_required
def tenant_dashboard_view(request):
    tenant = connection.tenant
    
    if tenant.schema_name == 'public':
        messages.error(request, 'Accede desde tu subdominio personalizado.')
        return redirect('unified_login')
    
    if not _validate_tenant_access(request, tenant):
        return redirect('unified_login')
    
    return render(request, 'dashboard/home.html', {
        'tenant': tenant,
        'page_title': f'Dashboard - {tenant.name}',
    })


def tenant_logout_view(request):
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'¡Hasta pronto, {user_name}!')
    
    return redirect('unified_login')


def _handle_authenticated_user(request, current_tenant):
    user_tenant = getattr(request.user, 'tenant', None)
    if user_tenant and user_tenant.id == current_tenant.id:
        return redirect('dashboard:home')
    
    messages.error(request, 'No tienes acceso a este espacio de trabajo.')
    logout(request)
    return redirect('unified_login')


def _validate_tenant_access(request, tenant):
    if not tenant.is_active:
        messages.error(request, 'Este espacio de trabajo no está disponible.')
        logout(request)
        return False
    
    user_tenant = getattr(request.user, 'tenant', None)
    if not user_tenant or user_tenant.id != tenant.id:
        messages.error(request, 'No tienes acceso a este espacio de trabajo.')
        logout(request)
        return False
    
    return True


def _process_login(request, current_tenant):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not (username and password):
        messages.error(request, 'Por favor, completa todos los campos')
        return _render_login_form(current_tenant, request)
    
    user = authenticate(request, username=username, password=password)
    if not user:
        messages.error(request, 'Usuario o contraseña incorrectos')
        return _render_login_form(current_tenant, request)
    
    user_tenant = getattr(user, 'tenant', None)
    if not user_tenant:
        messages.error(request, 'Tu usuario no tiene un espacio de trabajo asignado.')
        return _render_login_form(current_tenant, request)
    
    if user_tenant.id != current_tenant.id:
        messages.error(request, 'No tienes acceso a este espacio de trabajo.')
        return _render_login_form(current_tenant, request)
    
    if not user_tenant.is_available:
        messages.error(request, 'Tu espacio de trabajo no está activo.')
        return _render_login_form(current_tenant, request)
    
    login(request, user)
    messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
    return redirect('dashboard:home')


def _render_login_form(current_tenant, request=None):
    from django.shortcuts import render
    return render(request, 'authentication/tenant_login.html', {
        'page_title': f'Acceso - {current_tenant.name}',
        'tenant': current_tenant,
    })
