from django.urls import path
from Taskapp.views.api_views import task_api_views, task_request_api_views

urlpatterns = [
    path('api/tasks/', task_api_views.api_get_tasks, name='api_get_tasks'),
    path('api/tasks/update-status/', task_api_views.api_update_task_status, name='api_update_task_status'),
    path('api/tasks/assign/', task_api_views.api_assign_task, name='api_assign_task'),
    path('api/tasks/request/create/', task_request_api_views.api_submit_task_request, name='api_submit_task_request'),
    path('api/tasks/requests/', task_request_api_views.api_get_task_requests, name='api_get_task_requests'),
    path('api/tasks/request/approve/', task_request_api_views.api_approve_task_request, name='api_approve_task_request'),
    path('api/tasks/request/reject/', task_request_api_views.api_reject_task_request, name='api_reject_task_request'),
    path('api/notifications/', task_request_api_views.api_get_notifications, name='api_get_notifications'),
    path('api/notifications/mark-read/', task_request_api_views.api_mark_notifications_read, name='api_mark_notifications_read'),
]

