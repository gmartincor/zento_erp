from django.shortcuts import render


def dashboard_home(request):
    """Vista temporal del dashboard."""
    return render(request, 'dashboard/home.html', {'page_title': 'Dashboard'})
