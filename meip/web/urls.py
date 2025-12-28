from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('manual/', views.manual_validate, name='manual_validate'),
    path('batches/', views.batch_list, name='batch_list'),
    path('upload/', views.upload_batch, name='upload_batch'),
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('batch/<int:batch_id>/export', views.export_batch_csv, name='export_batch_csv'),
    path('batch/<int:batch_id>/recheck/', views.recheck_batch, name='recheck_batch'),
    path('batch/<int:batch_id>/delete/', views.delete_batch, name='delete_batch'),
    path('batch/<int:batch_id>/pause/', views.pause_batch, name='pause_batch'),
    path('batch/<int:batch_id>/resume/', views.resume_batch, name='resume_batch'),
    path('api/batch/<int:batch_id>/status/', views.batch_status_api, name='batch_status_api'),
    path('batch/bulk-action/', views.batch_bulk_action, name='batch_bulk_action'),
    path('management/', views.management, name='management'),
    path('api/system-health/', views.system_health_api, name='system_health_api'),
]
