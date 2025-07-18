from django.http import JsonResponse
from django.conf import settings
import os


def debug_main_view(request):
    """Debug view to check template and static files issues."""
    
    try:
        # Check static files
        static_files_info = {}
        
        # Check if static files exist
        static_css_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'css', 'style.css')
        static_files_info['style_css_path'] = static_css_path
        static_files_info['style_css_exists'] = os.path.exists(static_css_path)
        
        # Check if source CSS exists
        source_css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'style.css')
        static_files_info['source_css_path'] = source_css_path
        static_files_info['source_css_exists'] = os.path.exists(source_css_path)
        
        # Check static settings
        static_files_info['STATIC_ROOT'] = str(settings.STATIC_ROOT) if settings.STATIC_ROOT else None
        static_files_info['STATIC_URL'] = settings.STATIC_URL
        
        # List static css directory contents
        try:
            static_css_dir = os.path.join(settings.BASE_DIR, 'static', 'css')
            if os.path.exists(static_css_dir):
                static_files_info['css_dir_contents'] = os.listdir(static_css_dir)
            else:
                static_files_info['css_dir_contents'] = "Directory does not exist"
        except Exception as e:
            static_files_info['css_dir_error'] = str(e)
        
        return JsonResponse({
            'status': 'debug_ok',
            'static_files': static_files_info,
            'settings': {
                'DEBUG': settings.DEBUG,
                'BASE_DIR': str(settings.BASE_DIR),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'debug_error',
            'error': str(e),
            'error_type': type(e).__name__
        })
