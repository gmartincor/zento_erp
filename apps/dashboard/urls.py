from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('api/business-lines/', views.get_filtered_business_lines, name='filtered_business_lines'),
    path('api/expenses/', views.get_filtered_expenses, name='filtered_expenses'),
]
