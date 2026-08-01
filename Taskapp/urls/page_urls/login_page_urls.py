from django.urls import path
from Taskapp.views.page_views.login_page_views import login

urlpatterns = [
    path('', login, name='login'),
]


