from django.urls import path  # type: ignore[import]
from .views import get_log_content, download_log

urlpatterns = [
    path('logs/', get_log_content),
    path('logs/download/', download_log),
]
