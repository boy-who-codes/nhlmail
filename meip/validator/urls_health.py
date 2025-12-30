from django.urls import path
from .views_health import SystemHealthView

urlpatterns = [
    path('', SystemHealthView.as_view(), name='system_health'),
]
