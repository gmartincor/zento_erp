from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_tenants.utils import connection
from django.http import Http404
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    """Vista de login para tenants específicos solamente"""
    current_tenant = connection.tenant
    
    # Si estamos en el tenant público, mostrar página informativa (no login)
    if current_tenant.schema_name == 'public':
        return render(request, 'tenants/public_info.html', {
            'page_title': 'Nutrition Pro CRM - Sistema de Gestión',
        })
    
    # Si el usuario ya está autenticado y está en su tenant correcto, ir al dashboard
    if request.user.is_authenticated:
        user_tenant = getattr(request.user, 'tenant', None)
        if user_tenant and user_tenant.id == current_tenant.id:
            return redirect('tenant_dashboard')
        else:
            # Usuario autenticado pero en tenant incorrecto - hacer logout
            messages.error(request, 'No tienes acceso a este espacio de trabajo.')
            logout(request)
    
    if request.method == 'POST':
        return _process_tenant_login(request, current_tenant)
    
    context = {
        'page_title': f'Acceso - {current_tenant.name}',
        'tenant': current_tenant,
    }
    
    return render(request, 'authentication/tenant_login.html', context)


@login_required
def tenant_dashboard_view(request):
    """Vista del dashboard del tenant"""
    tenant = connection.tenant
    
    # Solo permitir acceso si estamos en un tenant válido y activo
    if tenant.schema_name == 'public':
        messages.error(request, 'Accede desde tu subdominio personalizado.')
        return redirect('unified_login')
    
    if not tenant.is_active:
        messages.error(request, 'Este espacio de trabajo no está disponible.')
        logout(request)
        return redirect('unified_login')
    
    # Verificar que el usuario pertenece a este tenant
    user_tenant = getattr(request.user, 'tenant', None)
    if not user_tenant or user_tenant.id != tenant.id:
        messages.error(request, 'No tienes acceso a este espacio de trabajo.')
        logout(request)
        return redirect('unified_login')
    
    context = {
        'tenant': tenant,
        'page_title': f'Dashboard - {tenant.name}',
    }
    
    return render(request, 'dashboard/home.html', context)


def tenant_logout_view(request):
    """Vista de logout"""
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'¡Hasta pronto, {user_name}!')
    
    return redirect('unified_login')


def _process_tenant_login(request, current_tenant):
    """Procesa el login en un tenant específico"""
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not (username and password):
        messages.error(request, 'Por favor, completa todos los campos')
        return render(request, 'authentication/tenant_login.html', {
            'page_title': f'Acceso - {current_tenant.name}',
            'tenant': current_tenant,
        })
    
    # Autenticar usuario
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, 'Usuario o contraseña incorrectos')
        return render(request, 'authentication/tenant_login.html', {
            'page_title': f'Acceso - {current_tenant.name}',
            'tenant': current_tenant,
        })
    
    # Verificar que el usuario pertenece a este tenant específico
    user_tenant = getattr(user, 'tenant', None)
    if not user_tenant:
        messages.error(request, 'Tu usuario no tiene un espacio de trabajo asignado.')
        return render(request, 'authentication/tenant_login.html', {
            'page_title': f'Acceso - {current_tenant.name}',
            'tenant': current_tenant,
        })
    
    if user_tenant.id != current_tenant.id:
        messages.error(request, 'No tienes acceso a este espacio de trabajo.')
        return render(request, 'authentication/tenant_login.html', {
            'page_title': f'Acceso - {current_tenant.name}',
            'tenant': current_tenant,
        })
    
    if not user_tenant.is_available:
        messages.error(request, 'Tu espacio de trabajo no está activo.')
        return render(request, 'authentication/tenant_login.html', {
            'page_title': f'Acceso - {current_tenant.name}',
            'tenant': current_tenant,
        })
    
    # Login exitoso
    login(request, user)
    messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
    return redirect('tenant_dashboard')
