from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Vista principal de categorías con totales
    path('', views.ExpenseCategoryView.as_view(), name='categories'),
    
    # Lista de gastos filtrada por categoría
    path('category/<str:category_type>/', views.ExpenseListView.as_view(), name='by-category'),
    
    # CRUD para gastos específicos por categoría
    path('category/<str:category_type>/create/', views.ExpenseCreateView.as_view(), name='create'),
    path('category/<str:category_type>/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='edit'),
    path('category/<str:category_type>/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='delete'),
]
