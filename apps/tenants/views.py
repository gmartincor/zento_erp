from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_tenants.utils import connection
from django.http import Http404
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    """Vista de login unificada que funciona en cualquier tenant"""
    current_tenant = connection.tenant
    
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        # Verificar que el usuario pertenece a este tenant o está en público
        if current_tenant.schema_name == 'public':
            # En tenant público, verificar si el usuario tiene tenant
            user_tenant = getattr(request.user, 'tenant', None)
            if user_tenant and user_tenant.is_available:
                messages.info(request, 'Ya tienes una sesión activa. Accede a tu área desde tu subdominio.')
                return render(request, 'authentication/login.html', {
                    'page_title': 'Acceso - Nutrition Pro CRM',
                    'user_has_tenant': True,
                    'user_tenant': user_tenant,
                })
        else:
            # En un tenant específico, ir al dashboard
            return redirect('tenant_dashboard')
    
    if request.method == 'POST':
        return _process_login_form(request, current_tenant)
    
    context = {
        'page_title': 'Acceso - Nutrition Pro CRM',
        'is_public_tenant': current_tenant.schema_name == 'public',
    }
    
    return render(request, 'authentication/login.html', context)


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


def _process_login_form(request, current_tenant):
    """Procesa el formulario de login"""
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not (username and password):
        messages.error(request, 'Por favor, completa todos los campos')
        return render(request, 'authentication/login.html', {
            'page_title': 'Acceso - Nutrition Pro CRM',
            'is_public_tenant': current_tenant.schema_name == 'public',
        })
    
    # Autenticar usuario
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, 'Usuario o contraseña incorrectos')
        return render(request, 'authentication/login.html', {
            'page_title': 'Acceso - Nutrition Pro CRM',
            'is_public_tenant': current_tenant.schema_name == 'public',
        })
    
    # Verificar que el usuario tiene un tenant asociado y está activo
    user_tenant = getattr(user, 'tenant', None)
    if not user_tenant or not user_tenant.is_available:
        messages.error(request, 'Tu cuenta no tiene un espacio de trabajo asignado o no está activa.')
        return render(request, 'authentication/login.html', {
            'page_title': 'Acceso - Nutrition Pro CRM',
            'is_public_tenant': current_tenant.schema_name == 'public',
        })
    
    # Login exitoso
    login(request, user)
    messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
    
    # Si estamos en el tenant correcto, ir al dashboard
    if current_tenant.id == user_tenant.id:
        return redirect('tenant_dashboard')
    
    # Si estamos en tenant público, mostrar mensaje para ir al subdominio
    if current_tenant.schema_name == 'public':
        messages.info(request, 'Accede a tu área de trabajo desde tu subdominio personalizado.')
        return render(request, 'authentication/login.html', {
            'page_title': 'Acceso - Nutrition Pro CRM',
            'user_has_tenant': True,
            'user_tenant': user_tenant,
            'is_public_tenant': True,
        })
    
    # Si estamos en un tenant incorrecto, mostrar error
    messages.error(request, 'Este no es tu espacio de trabajo. Accede desde tu subdominio.')
    logout(request)
    return redirect('unified_login')
