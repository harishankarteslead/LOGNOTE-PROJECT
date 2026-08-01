from django.urls import path
from Taskapp.views.page_views.superadmin_dashboard_views import superadmin_dashboard

urlpatterns = [
    path('superadmin-dashboard/', superadmin_dashboard, name='superadmin_dashboard'),
]