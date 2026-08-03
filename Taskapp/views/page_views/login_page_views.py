from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service

def login(request):
    if request.method == 'GET' and request.session.get('role'):
        return redirect('dashboard')

    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '').strip()

        user = employee_service.authenticate_user(username_input, password_input)

        if user:
            request.session['user_id'] = user['id']
            request.session['username'] = user['username']
            request.session['role'] = user['role']

            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'login.html')

    return render(request, 'login.html')
