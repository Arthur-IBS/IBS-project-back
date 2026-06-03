from django.urls import path
from .views import get_log_content,export_logs_csv, manage_log_location
 
urlpatterns = [
    path('logs/', get_log_content),
    path('logs/export/', export_logs_csv),
    path('config/', manage_log_location),
]
 