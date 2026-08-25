from django.urls import path
from Taskapp.views.api_views import task_api_views

urlpatterns = [
    path('api/tasks/', task_api_views.api_get_tasks, name='api_get_tasks'),
    path('api/tasks/update-status/', task_api_views.api_update_task_status, name='api_update_task_status'),
    path('api/tasks/assign/', task_api_views.api_assign_task, name='api_assign_task'),
]
