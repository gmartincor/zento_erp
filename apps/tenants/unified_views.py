from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django_tenants.utils import connection, get_tenant_model
from django.http import Http404
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    if request.user.is_authenticated:
        return _redirect_authenticated_user(request)
    
    if request.method == 'POST':
        return _process_login_form(request)
    
    context = {
        'page_title': 'Acceso - Nutrition Pro CRM',
        'show_unified_branding': True,
    }
    
    return render(request, 'authentication/login.html', context)


@login_required
def tenant_dashboard_view(request):
    tenant = connection.tenant
    
    if not tenant or not tenant.is_active:
        messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
        return redirect('unified_login')
    
    context = {
        'tenant': tenant,
        'page_title': f'Dashboard - {tenant.name}',
        'show_tenant_branding': True,
    }
    
    return render(request, 'dashboard/home.html', context)


def tenant_logout_view(request):
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'¡Hasta pronto, {user_name}!')
    
    return redirect('unified_login')


def _redirect_authenticated_user(request):
    user_tenant = get_user_tenant(request.user)
    if user_tenant:
        domain = user_tenant.domains.first()
        if domain:
            return redirect(f"http://{domain.domain}")
    
    messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
    return redirect('unified_login')


def _process_login_form(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    if not (username and password):
        messages.error(request, 'Por favor, completa todos los campos')
        return render(request, 'authentication/login.html', {'page_title': 'Acceso - Nutrition Pro CRM'})
    
    user = authenticate(request, username=username, password=password)
    if user is None:
        messages.error(request, 'Usuario o contraseña incorrectos')
        return render(request, 'authentication/login.html', {'page_title': 'Acceso - Nutrition Pro CRM'})
    
    user_tenant = get_user_tenant(user)
    if not user_tenant:
        messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
        return render(request, 'authentication/login.html', {'page_title': 'Acceso - Nutrition Pro CRM'})
    
    login(request, user)
    messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
    
    domain = user_tenant.domains.first()
    if domain:
        return redirect(f"http://{domain.domain}")
    
    messages.error(request, 'Configuración de dominio no disponible.')
    return redirect('unified_login')


def get_user_tenant(user):
    if hasattr(user, 'profile') and user.profile and hasattr(user.profile, 'tenant'):
        return user.profile.tenant
    
    try:
        return Tenant.objects.get(
            email=user.email,
            is_active=True,
            is_deleted=False
        )
    except Tenant.DoesNotExist:
        return None
