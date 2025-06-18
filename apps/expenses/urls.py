from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Vista principal de categorías con totales
    path('', views.ExpenseCategoryView.as_view(), name='categories'),
    
    # CRUD para categorías de gastos
    path('categories/create/', views.ExpenseCategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', views.ExpenseCategoryUpdateView.as_view(), name='category-edit'),
    path('categories/<int:pk>/delete/', views.ExpenseCategoryDeleteView.as_view(), name='category-delete'),
    
    # Vista de cards filtradas por tipo de categoría (FIXED, VARIABLE, etc.)
    path('type/<str:category_type>/', views.ExpenseCategoryByTypeView.as_view(), name='by-type'),
    
    # Lista de gastos filtrada por categoría específica
    path('category/<slug:category_slug>/', views.ExpenseListView.as_view(), name='by-category'),
    
    # CRUD para gastos específicos por categoría
    path('category/<slug:category_slug>/create/', views.ExpenseCreateView.as_view(), name='create'),
    path('category/<slug:category_slug>/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='edit'),
    path('category/<slug:category_slug>/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='delete'),
]
