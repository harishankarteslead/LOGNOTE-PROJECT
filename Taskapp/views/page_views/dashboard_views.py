from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service, task_service


def dashboard(request):
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_role or not user_id:
        messages.error(request, 'Please log in to access the dashboard.')
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'add':
            new_username = request.POST.get('username', '').strip()
            new_password = request.POST.get('password', '').strip()
            new_email = request.POST.get('email', '').strip()

            if user_role == 'superadmin':
                role = request.POST.get('role', 'employee').strip()
            else:
                role = 'employee'

            if not new_username or not new_password or not new_email:
                messages.error(request, 'All fields (Username, Password, Email) are required.')
            else:
                try:
                    employee_service.insert_user(new_username, new_password, new_email, role)
                    messages.success(request, f'{role.capitalize()} "{new_username}" created successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to create user: {str(e)}')
            return redirect('dashboard')

        elif action == 'edit':
            target_user_id = request.POST.get('user_id', '')
            new_username = request.POST.get('username', '').strip()
            new_password = request.POST.get('password', '').strip()
            new_email = request.POST.get('email', '').strip()

            if user_role == 'superadmin':
                role = request.POST.get('role', 'employee').strip()
            else:
                role = 'employee'

            if not target_user_id or not new_username or not new_email or not new_password:
                messages.error(request, 'All fields (Username, Email, Password) are required for update.')
            else:
                try:
                    employee_service.update_user(int(target_user_id), new_username, new_email, new_password, role)
                    messages.success(request, f'User "{new_username}" updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update user: {str(e)}')
            return redirect('dashboard')

        elif action == 'delete':
            target_user_id = request.POST.get('user_id', '')
            if target_user_id:
                try:
                    employee_service.delete_user(int(target_user_id))
                    messages.success(request, 'User deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to delete user: {str(e)}')
            return redirect('dashboard')

        elif action == 'assign_task':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')

            task_name = request.POST.get('task_name', '').strip()
            description = request.POST.get('description', '').strip()
            assigned_to_id = request.POST.get('assigned_to_id', '').strip()
            employee_name = request.POST.get('employee_name', '').strip()
            due_date = request.POST.get('due_date', '').strip() or None
            status = request.POST.get('status', 'Pending').strip()

            if not task_name or not assigned_to_id or not employee_name:
                messages.error(request, 'Task Name, Assigned To, and Employee Name are required fields.')
            else:
                try:
                    new_task_id = task_service.create_task(
                        task_name=task_name,
                        description=description,
                        assigned_to_id=int(assigned_to_id),
                        employee_name=employee_name,
                        due_date=due_date,
                        status=status
                    )
                    messages.success(request, f'Task #{new_task_id} ("{task_name}") assigned to {employee_name} successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to assign task: {str(e)}')
            return redirect('dashboard')

        elif action == 'update_task_status':
            task_id = request.POST.get('task_id', '')
            new_status = request.POST.get('status', '').strip()
            if task_id and new_status:
                try:
                    task_service.update_task_status(int(task_id), new_status)
                    messages.success(request, f'Task #{task_id} status updated to "{new_status}".')
                except Exception as e:
                    messages.error(request, f'Failed to update task status: {str(e)}')
            return redirect('dashboard')

        elif action == 'delete_task':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            task_id = request.POST.get('task_id', '')
            if task_id:
                try:
                    task_service.delete_task(int(task_id))
                    messages.success(request, f'Task #{task_id} deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to delete task: {str(e)}')
            return redirect('dashboard')

    # Fetch data based on role
    context = {
        'username': username,
        'role': user_role,
        'user_id': user_id,
    }

    # Retrieve tasks & employees lists
    all_assignable_employees = employee_service.get_users_by_role('employee')
    context['all_assignable_employees'] = all_assignable_employees

    if user_role in ('superadmin', 'admin'):
        tasks = task_service.get_all_tasks()
        context['tasks'] = tasks
        context['total_tasks'] = len(tasks)
    else:
        # Employee role
        tasks = task_service.get_tasks_by_employee(user_id, username)
        context['tasks'] = tasks
        context['total_tasks'] = len(tasks)

    if user_role == 'superadmin':
        all_users = employee_service.get_all_users()
        admins = [u for u in all_users if u['role'] == 'admin']
        employees = [u for u in all_users if u['role'] == 'employee']
        context.update({
            'all_users': all_users,
            'admins': admins,
            'employees': employees,
            'total_users': len(all_users),
            'total_admins': len(admins),
            'total_employees': len(employees),
        })
    elif user_role == 'admin':
        employees = employee_service.get_users_by_role('employee')
        context.update({
            'employees': employees,
            'total_employees': len(employees),
        })
    elif user_role == 'employee':
        user_info = employee_service.get_user_by_id(user_id)
        context.update({
            'user_info': user_info,
        })

    return render(request, 'dashboard.html', context)
