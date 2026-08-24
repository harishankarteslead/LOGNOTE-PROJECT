from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service

def login(request):
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
            return render(request, 'login.html', {
                'error': 'Invalid username or password.',
                'username': username_input
            })

    return render(request, 'login.html')
