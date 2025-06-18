from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse


def login_view(request):
    """Vista de login personalizada"""
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido/a, {user.get_full_name() or user.username}!')
                next_url = request.GET.get('next', 'dashboard:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Credenciales inválidas. Por favor, verifica tu usuario y contraseña.')
        else:
            messages.error(request, 'Por favor, completa todos los campos.')
    
    return render(request, 'authentication/login.html')


@login_required
def logout_view(request):
    """Vista de logout"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'¡Hasta pronto, {user_name}!')
    return redirect('authentication:login')
