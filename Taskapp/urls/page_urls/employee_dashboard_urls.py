from django.urls import path
from Taskapp.views.page_views.employee_dashboard_views import employee_dashboard

urlpatterns = [
    path('employee-dashboard/', employee_dashboard, name='employee_dashboard'),
]