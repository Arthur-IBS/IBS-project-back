from django.urls import path
from .views import get_log_content, set_log_location, update_log_location
 
urlpatterns = [
    path('logs/', get_log_content),
    path('config/', set_log_location),
    path('config/<int:pk>/', update_log_location),
]
 