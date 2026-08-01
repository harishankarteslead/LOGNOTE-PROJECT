from django.urls import path
from Taskapp.views.page_views.logout_views import logout_view

urlpatterns = [
    path('logout/', logout_view, name='logout')
]