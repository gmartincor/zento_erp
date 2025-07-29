from django.urls import path
from .views.export_views import export_data

app_name = 'core'

urlpatterns = [
    path('export/', export_data, name='export_data'),
]
