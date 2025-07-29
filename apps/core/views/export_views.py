from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from apps.core.services.tenant_export_engine import ExportManager


@login_required
@require_http_methods(["GET"])
def export_data(request):
    format_type = request.GET.get('format', 'excel')
    
    if format_type not in ['csv', 'zip', 'excel', 'json']:
        return HttpResponseBadRequest('Invalid format')
    
    try:
        exporter = ExportManager.create_export(format=format_type)
        export_data = exporter.export_all()
        filename = exporter.get_filename()
        
        content_types = {
            'csv': 'text/csv',
            'zip': 'application/zip',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'json': 'application/json'
        }
        
        response = HttpResponse(
            export_data,
            content_type=content_types[format_type]
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return HttpResponseBadRequest(f'Export failed: {str(e)}')
