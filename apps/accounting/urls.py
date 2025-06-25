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
    payment_list,
    payment_detail,
    payment_update,
    payment_mark_paid,
    payment_cancel,
    service_payment_history,
    service_renewal,
    payment_create,
    expiring_services
)
from .views.payment_history import payment_history_view

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
    
    # Payment History
    path('payments/history/', payment_history_view, name='payment_history'),
    
    # Payment URLs
    path('payments/', payment_list, name='payments'),
    path('payments/<int:payment_id>/', payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/edit/', payment_update, name='payment_update'),
    path('payments/<int:payment_id>/mark-paid/', payment_mark_paid, name='payment_mark_paid'),
    path('payments/<int:payment_id>/cancel/', payment_cancel, name='payment_cancel'),
    
    # Service payment management
    path('services/<int:service_id>/payments/', service_payment_history, name='service_payment_history'),
    path('services/<int:service_id>/renew/', service_renewal, name='service_renewal'),
    path('services/<int:service_id>/payments/create/', payment_create, name='payment_create'),
    
    # Expiring services
    path('expiring-services/', expiring_services, name='expiring_services'),
    
    # Business line specific payments
    re_path(
        r'^business-lines/(?P<business_line_path>[\w-]+(?:/[\w-]+)*)/payments/$',
        payment_list,
        name='business_line_payments'
    ),
]
