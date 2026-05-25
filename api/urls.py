from django.urls import path
from .views import get_log_content, manage_log_location
 
urlpatterns = [
    path('logs/', get_log_content),
    path('config/', manage_log_location),
]
 