from django.urls import path
from Taskapp.views.page_views.assigned_tasks_views import assigned_tasks_view

urlpatterns = [
    path('assigned-tasks/', assigned_tasks_view, name='assigned_tasks'),
]
