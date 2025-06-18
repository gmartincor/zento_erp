"""
URL configuration for accounting module.
Supports hierarchical navigation through business lines.
"""

from django.urls import path, re_path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard - Main entry point
    path('', views.AccountingDashboardView.as_view(), name='index'),
    
    # Hierarchical navigation system
    path('hierarchy/', views.BusinessLineHierarchyView.as_view(), name='hierarchy'),
    re_path(
        r'^hierarchy/(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        views.BusinessLineHierarchyView.as_view(),
        name='hierarchy-path'
    ),
    
    # Business lines overview - Lista consolidada de todas las líneas de negocio (legacy)
    path('business-lines/', views.BusinessLineListView.as_view(), name='business-lines'),
    
    # Revenue analysis views (legacy - to be contextual)
    path('revenue/categories/', views.CategorySummaryView.as_view(), name='revenue-categories'),
    path('revenue/clients/', views.ClientRevenueView.as_view(), name='revenue-clients'),
    
    # Service creation - Most specific, must come first
    # Examples: jaen/pepe/pepe-normal/white/create/, jaen/pepe/pepe-normal/black/create/
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/create/$',
        views.ServiceCreateView.as_view(),
        name='service-create'
    ),
    
    # Service editing
    # Examples: jaen/pepe/pepe-normal/white/123/edit/, jaen/pepe/pepe-normal/black/456/edit/
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/(?P<service_id>\d+)/edit/$',
        views.ServiceEditView.as_view(),
        name='service-edit'
    ),
    
    # Service category lists - WHITE/BLACK services
    # Examples: jaen/pepe/pepe-normal/white/, jaen/pepe/pepe-normal/black/
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/$',
        views.ServiceCategoryListView.as_view(),
        name='category-services'
    ),
    
    # Business line detail - Supports any level of hierarchy
    # Examples: jaen/, jaen/pepe/, jaen/pepe/pepe-normal/
    # Must come AFTER category patterns to avoid conflicts
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        views.BusinessLineDetailView.as_view(),
        name='line-detail'
    ),
]
