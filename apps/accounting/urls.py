from django.urls import path, re_path
from . import views
from .views import payment_history

app_name = 'accounting'

urlpatterns = [
    path('', views.AccountingDashboardView.as_view(), name='index'),
    path('create/', views.BusinessLineCreateView.as_view(), name='create'),
    path('create/<int:parent>/', views.BusinessLineCreateView.as_view(), name='create-child'),
    path('revenue/categories/', views.CategorySummaryView.as_view(), name='revenue-categories'),
    path('revenue/clients/', views.ClientRevenueView.as_view(), name='revenue-clients'),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/create/$',
        views.ServiceCreateView.as_view(),
        name='service-create'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/(?P<service_id>\d+)/edit/$',
        views.ServiceEditView.as_view(),
        name='service-edit'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/$',
        views.ServiceCategoryListView.as_view(),
        name='category-services'
    ),
    path('business-lines/', views.BusinessLineHierarchyView.as_view(), name='business-lines'),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/create-subline/$',
        views.BusinessLineCreateView.as_view(),
        name='business_line_create_subline'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/edit/$',
        views.BusinessLineUpdateView.as_view(),
        name='business_line_edit'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/delete/$',
        views.BusinessLineDeleteView.as_view(),
        name='business_line_delete'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/manage/$',
        views.BusinessLineManagementDetailView.as_view(),
        name='business-line-manage'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        views.BusinessLineHierarchyView.as_view(),
        name='business-lines-path'
    ),
    
    # Payment History
    path('payments/history/', payment_history.payment_history_view, name='payment_history'),
    
    # Payment URLs
    path('payments/', views.payment_list, name='payments'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:payment_id>/mark-paid/', views.payment_mark_paid, name='payment_mark_paid'),
    path('payments/<int:payment_id>/cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Service payment management
    path('services/<int:service_id>/payments/', views.service_payment_history, name='service_payment_history'),
    path('services/<int:service_id>/renew/', views.service_renewal, name='service_renewal'),
    path('services/<int:service_id>/payments/create/', views.payment_create, name='payment_create'),
    
    # Expiring services
    path('expiring-services/', views.expiring_services, name='expiring_services'),
    
    # Business line specific payments
    re_path(
        r'^business-lines/(?P<business_line_path>[\w-]+(?:/[\w-]+)*)/payments/$',
        views.payment_list,
        name='business_line_payments'
    ),
]
