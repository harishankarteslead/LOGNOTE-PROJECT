from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service

def login(request):
    if request.method == 'GET' and request.session.get('role'):
        role = request.session.get('role')
        if role =='superadmin':
            return redirect('superadmin_dashboard')
        elif role =='admin':
            return redirect('admin_dashboard')
        elif role =='employee':
            return redirect('employee_dashboard')
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '').strip()

        user = employee_service.authenticate_user(username_input, password_input)

        if user:
            request.session['user_id'] = user['id']
            request.session['username'] = user['username']
            request.session['role'] = user['role']

            role = user['role']
            if role == 'superadmin':
                return redirect('superadmin_dashboard')
            elif role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'employee':
                return redirect('employee_dashboard')
            else:
                messages.error(request, 'Invalid user role assigned.')
                return render(request, 'login.html')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'login.html')

    return render(request, 'login.html')
