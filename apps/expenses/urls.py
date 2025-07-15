from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.ExpenseCategoryView.as_view(), name='default'),
    
    # Category management URLs (more specific patterns first)
    path('categories/create/', views.ExpenseCategoryCreateView.as_view(), name='category-create'),
    path('categories/<slug:category_slug>/edit/', views.ExpenseCategoryUpdateView.as_view(), name='category-edit'),
    path('categories/<slug:category_slug>/delete/', views.ExpenseCategoryDeleteView.as_view(), name='category-delete'),
    
    # Service category URLs (more generic patterns)
    path('<str:service_category>/', views.ExpenseCategoryView.as_view(), name='categories'),
    path('<str:service_category>/type/<str:category_type>/', views.ExpenseListView.as_view(), name='by-type'),
    path('<str:service_category>/create/', views.ExpenseCreateView.as_view(), name='create'),
    path('<str:service_category>/type/<str:category_type>/create/', views.ExpenseCreateView.as_view(), name='create-by-type'),
    path('<str:service_category>/category/<slug:category_slug>/', views.ExpenseListView.as_view(), name='by-category'),
    
    # Individual expense management
    path('<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='delete'),
]
