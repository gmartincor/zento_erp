from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import traceback


def health_check(request):
    try:
        # Verificar base de datos básica
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Verificar tenants (esto es lo que probablemente falla)
        tenant_status = "unknown"
        tenant_error = None
        
        try:
            from apps.tenants.models import Tenant, Domain
            tenant_count = Tenant.objects.count()
            domain_count = Domain.objects.count()
            tenant_status = f"OK: {tenant_count} tenants, {domain_count} domains"
        except Exception as e:
            tenant_error = str(e)
            tenant_status = f"ERROR: {tenant_error}"
        
        # Verificar content types
        ct_status = "unknown"
        try:
            from django.contrib.contenttypes.models import ContentType
            ct_count = ContentType.objects.count()
            ct_status = f"OK: {ct_count} content types"
        except Exception as e:
            ct_status = f"ERROR: {e}"
        
        return JsonResponse({
            "status": "healthy" if tenant_error is None else "degraded",
            "environment": getattr(settings, 'ENVIRONMENT', 'unknown'),
            "debug": settings.DEBUG,
            "database": "OK",
            "tenants": tenant_status,
            "content_types": ct_status,
            "tenant_error": tenant_error
        })
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc() if settings.DEBUG else None
        }, status=500)
