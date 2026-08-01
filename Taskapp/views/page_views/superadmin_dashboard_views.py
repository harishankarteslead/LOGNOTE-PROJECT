from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service


def superadmin_dashboard(request):
    if request.session.get('role') != 'superadmin':
        messages.error(request, 'Unauthorized access. Please login as Superadmin.')
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add':
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'employee').strip()

            if not username or not password or not email:
                messages.error(request, 'All fields (Username, Password, Email) are required.')
            else:
                try:
                    employee_service.insert_user(username, password, email, role)
                    messages.success(request, f'{role.capitalize()} "{username}" created successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to create user: {str(e)}')
            return redirect('superadmin_dashboard')

        elif action == 'edit':
            user_id = request.POST.get('user_id', '')
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'employee').strip()

            if not user_id or not username or not email or not password:
                messages.error(request, 'All fields (Username, Email, Password, Role) are required for update.')
            else:
                try:
                    employee_service.update_user(int(user_id), username, email, password, role)
                    messages.success(request, f'User "{username}" updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update user: {str(e)}')
            return redirect('superadmin_dashboard')

        elif action == 'delete':
            user_id = request.POST.get('user_id', '')
            if user_id:
                try:
                    employee_service.delete_user(int(user_id))
                    messages.success(request, 'User deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to delete user: {str(e)}')
            return redirect('superadmin_dashboard')

    all_users = employee_service.get_all_users()
    admins = [u for u in all_users if u['role'] == 'admin']
    employees = [u for u in all_users if u['role'] == 'employee']

    context = {
        'username': request.session.get('username'),
        'role': request.session.get('role'),
        'all_users': all_users,
        'admins': admins,
        'employees': employees,
        'total_users': len(all_users),
        'total_admins': len(admins),
        'total_employees': len(employees),
    }
    return render(request, 'superadmin_dashboard.html', context)


