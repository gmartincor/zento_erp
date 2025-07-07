from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.urls import reverse
from apps.authentication.models import User
from .models import Tenant


def unified_login_view(request):
    """
    Vista de login unificada que redirige a la ruta del tenant.
    
    Esta vista proporciona un único punto de entrada para todos los usuarios,
    independientemente del tenant al que pertenezcan. Después de la autenticación,
    los redirige a la ruta específica de su tenant.
    """
    
    # Si el usuario ya está autenticado, redirigirlo a su dashboard
    if request.user.is_authenticated:
        return _redirect_authenticated_user(request)
    
    # Procesamiento del formulario de login
    if request.method == 'POST':
        return _process_login_form(request)
    
    # Renderizar formulario de login
    context = {
        'page_title': 'Acceso - Nutrition Pro CRM',
        'show_unified_branding': True,
    }
    
    return render(request, 'authentication/login.html', context)


def _redirect_authenticated_user(request):
    """
    Redirige a un usuario ya autenticado a su dashboard.
    """
    user_tenant = get_user_tenant(request.user)
    if user_tenant:
        # Redirigir a la ruta del tenant (usando slug)
        tenant_url = reverse('dashboard_home', kwargs={'tenant_slug': user_tenant.slug})
        return redirect(tenant_url)
    else:
        messages.error(request, 'Acceso no disponible. Por favor, contacta al administrador.')
        return redirect('unified_login')


def _process_login_form(request):
    """
    Procesa el envío del formulario de login.
    """
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
    
    # Redirigir a la ruta del tenant (usando slug)
    tenant_url = reverse('dashboard_home', kwargs={'tenant_slug': user_tenant.slug})
    return redirect(tenant_url)


def get_user_tenant(user):
    """
    Obtiene el tenant asociado a un usuario.
    Cada nutricionista (tenant) tiene un único usuario asociado.
    
    Args:
        user: El objeto usuario
        
    Returns:
        El objeto tenant asociado o None si no se encuentra
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
