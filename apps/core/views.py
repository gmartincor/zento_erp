from django.http import JsonResponse
from django.db import connection
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime

@never_cache
@csrf_exempt  
def home_view(request):
    """Vista simple para la raíz del sitio"""
    return JsonResponse({
        "message": "Zento ERP API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "tenant": getattr(request, 'tenant', None) and request.tenant.schema_name or "unknown"
    }, status=200)

@never_cache
@csrf_exempt
def health_check(request):
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Basic health status
        health_status = {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
        
        return JsonResponse(health_status, status=200)
    
    except Exception as e:
        # Return unhealthy status
        health_status = {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "timestamp": datetime.now().isoformat()
        }
        
        return JsonResponse(health_status, status=503)
