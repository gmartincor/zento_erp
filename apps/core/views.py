from django.http import JsonResponse
from datetime import datetime

def home_view(request):
    """Vista simple para la raíz del sitio"""
    return JsonResponse({
        "message": "Zento ERP API",
        "version": "1.0.0", 
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "tenant": getattr(request, 'tenant', None) and request.tenant.schema_name or "unknown"
    }, status=200)
