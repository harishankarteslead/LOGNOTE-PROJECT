from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service


def admin_dashboard(request):
    if request.session.get('role') != 'admin':
        messages.error(request, 'Unauthorized access. Please login as Admin.')
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
            role = 'employee'

            if not username or not password or not email:
                messages.error(request, 'All fields (Username, Password, Email) are required.')
            else:
                try:
                    employee_service.insert_user(username, password, email, role)
                    messages.success(request, f'Employee "{username}" created successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to create employee: {str(e)}')
            return redirect('admin_dashboard')

        elif action == 'edit':
            user_id = request.POST.get('user_id', '')
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
            role = 'employee'

            if not user_id or not username or not email or not password:
                messages.error(request, 'All fields (Username, Email, Password) are required for update.')
            else:
                try:
                    employee_service.update_user(int(user_id), username, email, password, role)
                    messages.success(request, f'Employee "{username}" updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update employee: {str(e)}')
            return redirect('admin_dashboard')

        elif action == 'delete':
            user_id = request.POST.get('user_id', '')
            if user_id:
                try:
                    employee_service.delete_user(int(user_id))
                    messages.success(request, 'Employee deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to delete employee: {str(e)}')
            return redirect('admin_dashboard')

    employees = employee_service.get_users_by_role('employee')

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'employees': employees,
        'total_employees': len(employees),
    }
    return render(request, 'admin_dashboard.html', context)

