from django.urls import path, re_path
from django.views.generic import RedirectView
from .views import (
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
    ExpiringServicesView,
    PaymentRefundView
)
from .views.payment_history import payment_history_view
from .views.client_service_history import ClientServiceHistoryView, ClientServiceDetailView
from .views.service_renewal import service_renewal_view
from .views.service_termination import service_termination_view
from .views.service_payment import (
    service_payment_view,
    ajax_get_suggested_amount,
    payment_options_view,
    service_payment_history_view,
)
from .views.payment_detail import payment_detail_view
from .views.remanentes_summary import remanentes_summary_view

app_name = 'accounting'

urlpatterns = [
    # Redirect root accounting URL to business lines management
    path('', RedirectView.as_view(pattern_name='accounting:business-lines', permanent=True), name='index'),
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
    path('clients/<int:client_id>/services/', ClientServiceHistoryView.as_view(), name='client-service-history'),
    path('services/<int:service_id>/detail/', ClientServiceDetailView.as_view(), name='client-service-detail'),
    
    path('services/<int:service_id>/renewal/', service_renewal_view, name='service-renewal'),
    path('services/<int:service_id>/terminate/', service_termination_view, name='service-terminate'),
    
    path('services/<int:service_id>/payment/', service_payment_view, name='service-payment'),
    path('services/<int:service_id>/payment/options/', payment_options_view, name='payment-options'),
    path('services/<int:service_id>/payment/history/', service_payment_history_view, name='service-payment-history'),
    path('services/<int:service_id>/payment/ajax/suggested-amount/<int:period_id>/', ajax_get_suggested_amount, name='ajax-suggested-amount'),
    
    path('payments/<int:payment_id>/', payment_detail_view, name='payment-detail'),
    path('payments/<int:payment_id>/refund/', PaymentRefundView.as_view(), name='payment-refund'),
    
    path('remanentes/', remanentes_summary_view, name='remanentes-summary'),
    
]
