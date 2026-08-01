from django.urls import path
from Taskapp.views.page_views.admin_dashboard_views import admin_dashboard

urlpatterns = [
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
]