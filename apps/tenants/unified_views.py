from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    """Vista de login unificada que redirige a la ruta del tenant"""
    
    if request.user.is_authenticated:
        user_tenant = get_user_tenant(request.user)
        if user_tenant:
            # Redirigir a la ruta del tenant (usando slug)
            tenant_url = reverse('dashboard_home', kwargs={'tenant_slug': user_tenant.slug})
            return redirect(tenant_url)
        else:
            messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
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
                    
                    # Redirigir a la ruta del tenant (usando slug)
                    tenant_url = reverse('dashboard_home', kwargs={'tenant_slug': user_tenant.slug})
                    return redirect(tenant_url)
                else:
                    messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos')
        else:
            messages.error(request, 'Por favor, completa todos los campos')
    
    context = {
        'page_title': 'Acceso - Nutrition Pro CRM',
        'show_unified_branding': True,
    }
    
    return render(request, 'authentication/login.html', context)


def get_user_tenant(user):
    """
    Obtiene el tenant asociado a un usuario.
    Cada nutricionista (tenant) tiene un único usuario asociado.
    """
    # Si el usuario tiene un perfil con tenant asignado
    if hasattr(user, 'profile') and user.profile and hasattr(user.profile, 'tenant'):
        return user.profile.tenant
    
    # Intentar encontrar por coincidencia de username y slug
    try:
        return Tenant.objects.get(
            slug=user.username,
            is_active=True,
            is_deleted=False
        )
    except Tenant.DoesNotExist:
        # Si no hay coincidencia, intentar por email
        try:
            return Tenant.objects.get(
                email=user.email,
                is_active=True,
                is_deleted=False
            )
        except Tenant.DoesNotExist:
            return None
