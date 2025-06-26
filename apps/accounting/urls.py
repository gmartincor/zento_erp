from django.urls import path, re_path
from .views import (
    AccountingDashboardView,
    BusinessLineCreateView,
    CategorySummaryView,
    ClientRevenueView,
    ServiceCreateView,
    ServiceEditView,
    ServiceCategoryListView,
    BusinessLineHierarchyView,
    BusinessLineUpdateView,
    BusinessLineDeleteView,
    BusinessLineManagementDetailView,
    PaymentManagementView,
    ExpiringServicesView
)
from .views.payment_history import payment_history_view
from .views.client_service_history import ClientServiceHistoryView, ClientServiceDetailView
from .views.service_payment import ServicePaymentView, ServiceRenewalView

app_name = 'accounting'

urlpatterns = [
    path('', AccountingDashboardView.as_view(), name='index'),
    path('create/', BusinessLineCreateView.as_view(), name='create'),
    path('create/<int:parent>/', BusinessLineCreateView.as_view(), name='create-child'),
    path('revenue/categories/', CategorySummaryView.as_view(), name='revenue-categories'),
    path('revenue/clients/', ClientRevenueView.as_view(), name='revenue-clients'),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/create/$',
        ServiceCreateView.as_view(),
        name='service-create'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/(?P<service_id>\d+)/edit/$',
        ServiceEditView.as_view(),
        name='service-edit'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/(?P<category>white|black)/$',
        ServiceCategoryListView.as_view(),
        name='category-services'
    ),
    path('business-lines/', BusinessLineHierarchyView.as_view(), name='business-lines'),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/create-subline/$',
        BusinessLineCreateView.as_view(),
        name='business_line_create_subline'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/edit/$',
        BusinessLineUpdateView.as_view(),
        name='business_line_edit'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/delete/$',
        BusinessLineDeleteView.as_view(),
        name='business_line_delete'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/manage/$',
        BusinessLineManagementDetailView.as_view(),
        name='business-line-manage'
    ),
    re_path(
        r'^business-lines/(?P<line_path>[\w-]+(?:/[\w-]+)*)/$',
        BusinessLineHierarchyView.as_view(),
        name='business-lines-path'
    ),
    
    # Payment Management
    path('payments/', PaymentManagementView.as_view(), name='payments'),
    path('payments/history/', payment_history_view, name='payment-history'),
    path('expiring-services/', ExpiringServicesView.as_view(), name='expiring_services'),
    
    # Client Service History
    path('payments/history/', payment_history_view, name='payment-history'),
    
    # Client Service History
    path('clients/<int:client_id>/services/', ClientServiceHistoryView.as_view(), name='client-service-history'),
    path('services/<int:service_id>/detail/', ClientServiceDetailView.as_view(), name='client-service-detail'),
    
    # Service Payment and Renewal URLs
    path('services/<int:service_id>/payment/', ServicePaymentView.as_view(), name='service-payment'),
    path('services/<int:service_id>/renewal/', ServiceRenewalView.as_view(), name='service-renewal'),
]
