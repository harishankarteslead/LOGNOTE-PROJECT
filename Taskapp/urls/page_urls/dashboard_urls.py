from django.urls import path
from Taskapp.views.page_views.dashboard_views import dashboard

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
]
