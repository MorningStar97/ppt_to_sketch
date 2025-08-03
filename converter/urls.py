from django.urls import path
from . import views

app_name = 'converter'

urlpatterns = [
    # API 端点
    path('api/tasks/', views.ConversionTaskListCreateView.as_view(), name='task-list-create'),
    path('api/tasks/<uuid:pk>/', views.ConversionTaskDetailView.as_view(), name='task-detail'),
    path('api/tasks/<uuid:task_id>/download/', views.download_sketch_file, name='download-sketch'),
    path('api/tasks/<uuid:task_id>/delete/', views.delete_conversion_task, name='delete-task'),
    
    # 前端页面
    path('', views.index_view, name='index'),
    path('tasks/', views.task_list_view, name='task-list'),
    path('tasks/<uuid:task_id>/', views.task_detail_view, name='task-detail'),
] 