from django.urls import path
from . import views

app_name = 'invoicing'

urlpatterns = [
    path('', views.InvoiceListView.as_view(), name='invoice_list'),
    path('create/', views.InvoiceCreateView.as_view(), name='invoice_create'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('<int:pk>/edit/', views.InvoiceUpdateView.as_view(), name='invoice_edit'),
    path('<int:pk>/pdf/', views.generate_pdf_view, name='invoice_pdf'),
    
    path('company/setup/', views.CompanyCreateView.as_view(), name='company_create'),
    path('company/edit/', views.CompanyUpdateView.as_view(), name='company_edit'),
]
