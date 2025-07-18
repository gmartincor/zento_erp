from django.http import JsonResponse
from django.db import connection
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
import json

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
            "timestamp": "2025-07-18T10:00:00Z"
        }
        
        return JsonResponse(health_status, status=200)
    
    except Exception as e:
        # Return unhealthy status
        health_status = {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected",
            "timestamp": "2025-07-18T10:00:00Z"
        }
        
        return JsonResponse(health_status, status=503)
