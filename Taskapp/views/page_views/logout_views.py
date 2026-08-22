from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service


def logout_view(request):
    request.session.flush()
    return redirect('login')