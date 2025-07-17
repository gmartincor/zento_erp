from django.http import JsonResponse
from django.db import connection
from django.conf import settings


def health_check(request):
    """
    Health check SIMPLE para Docker y Render
    """
    try:
        # Verificar base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            "status": "healthy",
            "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
            "debug": settings.DEBUG
        })
    
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status=503)
