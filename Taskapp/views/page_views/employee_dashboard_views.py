from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service


def employee_dashboard(request):
    if request.session.get('role') != 'employee':
        messages.error(request, 'Unauthorized access. Please login as Employee.')
        return redirect('login')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role')
    }
    return render(request, 'employee_dashboard.html', context)

