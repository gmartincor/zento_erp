from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.conf import settings


def tenant_login_view(request, tenant_slug):
    if not hasattr(request, 'tenant') or not request.tenant:
        messages.error(request, f'El tenant "{tenant_slug}" no existe o no está disponible')
        return redirect('admin:index')
    
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('tenant_dashboard', tenant_slug=tenant_slug)
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido/a a {request.tenant.name}, {user.get_full_name() or user.username}!')
            return redirect('tenant_dashboard', tenant_slug=tenant_slug)
        else:
            messages.error(request, 'Credenciales inválidas')
    
    context = {
        'tenant': request.tenant,
        'page_title': f'Acceso - {request.tenant.name}',
    }
    
    return render(request, 'authentication/login.html', context)


def tenant_dashboard_view(request, tenant_slug):
    if not hasattr(request, 'tenant') or not request.tenant:
        messages.error(request, 'Tenant no encontrado')
        return redirect('tenant_login', tenant_slug=tenant_slug)
    
    if not request.user.is_authenticated:
        return redirect('tenant_login', tenant_slug=tenant_slug)
    
    context = {
        'tenant': request.tenant,
        'page_title': f'Dashboard - {request.tenant.name}',
    }
    
    return render(request, 'dashboard/home.html', context)


def tenant_logout_view(request, tenant_slug):
    if not hasattr(request, 'tenant') or not request.tenant:
        messages.error(request, 'Tenant no encontrado')
        return redirect('tenant_login', tenant_slug=tenant_slug)
    
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'¡Hasta pronto, {user_name}!')
    
    return redirect('tenant_login', tenant_slug=tenant_slug)
