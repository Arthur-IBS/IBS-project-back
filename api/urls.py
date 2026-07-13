from django.urls import path
from . import views
 
urlpatterns = [
    path('logs/', views.get_log_content, name='get_log_content'),
    path('logs/latest/',views.get_latest_logs),
    path('logs/export/', views.export_logs_csv, name='export_logs_csv'),
    path('config/', views.manage_log_location, name='manage_log_location'),
    path('apps/', views.get_apps, name='get_apps'),
]