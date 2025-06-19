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
    
    # Revenue analysis views (legacy - to be contextual)
    path('revenue/categories/', views.CategorySummaryView.as_view(), name='revenue-categories'),
    path('revenue/clients/', views.ClientRevenueView.as_view(), name='revenue-clients'),
    
    # Service creation - MOST SPECIFIC, must come first
    # Examples: business-lines/jaen/pepe/pepe-normal/white/create/, business-lines/jaen/pepe/pepe-normal/black/create/
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/create/$',
        views.ServiceCreateView.as_view(),
        name='service-create'
    ),
    
    # Service editing - SECOND MOST SPECIFIC
    # Examples: business-lines/jaen/pepe/pepe-normal/white/123/edit/, business-lines/jaen/pepe/pepe-normal/black/456/edit/
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/(?P<service_id>\d+)/edit/$',
        views.ServiceEditView.as_view(),
        name='service-edit'
    ),
    
    # Service category lists - THIRD MOST SPECIFIC
    # Examples: business-lines/jaen/pepe/pepe-normal/white/, business-lines/jaen/pepe/pepe-normal/black/
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/$',
        views.ServiceCategoryListView.as_view(),
        name='category-services'
    ),
    
    # Business lines navigation - ROOT LEVEL
    path('business-lines/', views.BusinessLineHierarchyView.as_view(), name='business-lines'),
    
    # Business lines navigation - WITH PATH (LEAST SPECIFIC, must come last)
    # Examples: business-lines/jaen/, business-lines/jaen/pepe/, business-lines/jaen/pepe/pepe-normal/
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        views.BusinessLineHierarchyView.as_view(),
        name='business-lines-path'
    ),
]
