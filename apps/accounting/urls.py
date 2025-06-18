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
    
    # Business line detail - Supports any level of hierarchy
    # Examples: jaen/, jaen/pepe/, jaen/pepe/pepe-normal/
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        views.BusinessLineDetailView.as_view(),
        name='line-detail'
    ),
    
    # Service category lists - WHITE/BLACK services
    # Examples: jaen/pepe/pepe-normal/white/, jaen/pepe/pepe-normal/black/
    re_path(
        r'^(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/$',
        views.ServiceCategoryListView.as_view(),
        name='category-services'
    ),
    
    # Service creation
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
    
    # Additional utility URLs for AJAX calls or future features
    re_path(
        r'^api/(?P<line_path>[\w-]+(?:/[\w-]+)*)/stats/$',
        views.BusinessLineDetailView.as_view(),
        name='line-stats-api'
    ),
]
