from .public import urlpatterns as public_urlpatterns
from .tenants import urlpatterns as tenant_urlpatterns

__all__ = ['public_urlpatterns', 'tenant_urlpatterns']
