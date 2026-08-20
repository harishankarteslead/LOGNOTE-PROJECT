from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service, task_service, project_service


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
            return redirect('/dashboard/?tab=add-members')

        elif action == 'edit':
            target_user_id = request.POST.get('user_id', '')
            new_username = request.POST.get('username', '').strip()
            new_password = request.POST.get('password', '').strip()
            new_email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'employee').strip()

            if not target_user_id or not new_username or not new_email:
                messages.error(request, 'Username and Email are required.')
            else:
                try:
                    employee_service.update_user(int(target_user_id), new_username, new_email, new_password, role)
                    messages.success(request, f'User "{new_username}" updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update user: {str(e)}')
            return redirect('/dashboard/?tab=add-members')

        elif action == 'delete':
            target_user_id = request.POST.get('user_id', '')
            if target_user_id:
                try:
                    employee_service.delete_user(int(target_user_id))
                    messages.success(request, 'User deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to delete user: {str(e)}')
            return redirect('/dashboard/?tab=add-members')

        elif action == 'assign_task':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')

            task_name = request.POST.get('task_name', '').strip()
            project_name = request.POST.get('project_name', '').strip()
            description = request.POST.get('description', '').strip()
            assigned_to_ids = request.POST.getlist('assigned_to_ids')
            due_date = request.POST.get('due_date', '').strip() or None
            status = request.POST.get('status', '').strip() or 'Not Worked'

            if not task_name or not assigned_to_ids:
                messages.error(request, 'Atleast One Assigned Employee is Required.')
            else:
                try:
                    emp_list = []
                    for emp_id in assigned_to_ids:
                        emp = employee_service.get_user_by_id(int(emp_id))
                        if emp:
                            emp_list.append(emp)

                    if emp_list:
                        employee_names_str = ", ".join([e['username'] for e in emp_list])
                        primary_emp_id = emp_list[0]['id']
                        new_task_id = task_service.create_task(
                            task_name=task_name,
                            description=description,
                            assigned_to_id=primary_emp_id,
                            employee_name=employee_names_str,
                            due_date=due_date,
                            status=status,
                            project_name=project_name
                        )
                        messages.success(request, f'Task #{new_task_id} ("{task_name}") assigned to {employee_names_str} successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to assign task: {str(e)}')
            return redirect('/dashboard/?tab=form-data')

        elif action == 'update_task_status':
            task_id = request.POST.get('task_id', '')
            new_status = request.POST.get('status', '').strip()
            redirect_tab = request.POST.get('active_tab', 'dashboard')
            if task_id and new_status:
                try:
                    task_service.update_task_status(int(task_id), new_status)
                    messages.success(request, f'Task #{task_id} status updated to "{new_status}".')
                except Exception as e:
                    messages.error(request, f'Failed to update task status: {str(e)}')
            return redirect(f'/dashboard/?tab={redirect_tab}')

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
            return redirect('/dashboard/?tab=form-data')

        elif action == 'add_project':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            project_name = request.POST.get('project_name', '').strip()
            project_type = request.POST.get('project_type', '').strip()
            status = request.POST.get('status', '').strip() or 'Not Worked'
            start_date = request.POST.get('start_date', '').strip() or None
            due_date = request.POST.get('due_date', '').strip() or None
            actual_complete_date = request.POST.get('actual_complete_date', '').strip() or None
            description = request.POST.get('description', '').strip()

            if not project_name or not project_type:
                messages.error(request, 'Project Name and Project Type are required fields.')
            else:
                try:
                    new_proj_id = project_service.create_project(
                        project_name=project_name,
                        project_type=project_type,
                        status=status,
                        start_date=start_date,
                        due_date=due_date,
                        actual_complete_date=actual_complete_date,
                        description=description
                    )
                    messages.success(request, f'Project "{project_name}" (#{new_proj_id}) created successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to create project: {str(e)}')
            return redirect('/dashboard/?tab=add-project')

        elif action == 'delete_project':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            project_id = request.POST.get('project_id', '')
            if project_id:
                try:
                    project_service.delete_project(int(project_id))
                    messages.success(request, f'Project #{project_id} deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to delete project: {str(e)}')
            return redirect('/dashboard/?tab=add-project')

        elif action == 'update_project_status':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            project_id = request.POST.get('project_id', '')
            new_status = request.POST.get('status', '').strip()
            if project_id and new_status:
                try:
                    project_service.update_project_status(int(project_id), new_status)
                    messages.success(request, f'Project #{project_id} status updated to "{new_status}".')
                except Exception as e:
                    messages.error(request, f'Failed to update project status: {str(e)}')
            return redirect('/dashboard/?tab=add-project')


        elif action == 'edit_task':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')

            task_id = request.POST.get('task_id', '')
            task_name = request.POST.get('task_name', '').strip()
            project_name = request.POST.get('project_name', '').strip()
            description = request.POST.get('description', '').strip()
            assigned_to_ids = request.POST.getlist('assigned_to_ids')
            due_date = request.POST.get('due_date', '').strip() or None
            status = request.POST.get('status', '').strip() or 'Not Worked'

            if not task_id or not task_name or not assigned_to_ids:
                messages.error(request, 'Task ID, Task Name, and at least one Assigned Employee are required.')
            else:
                try:
                    emp_list = []
                    for emp_id in assigned_to_ids:
                        emp = employee_service.get_user_by_id(int(emp_id))
                        if emp:
                            emp_list.append(emp)

                    if emp_list:
                        employee_names_str = ", ".join([e['username'] for e in emp_list])
                        primary_emp_id = emp_list[0]['id']
                        task_service.update_task_details(
                            task_id=int(task_id),
                            task_name=task_name,
                            description=description,
                            assigned_to_id=primary_emp_id,
                            employee_name=employee_names_str,
                            due_date=due_date,
                            status=status,
                            project_name=project_name
                        )
                        messages.success(request, f'Task #{task_id} updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update task: {str(e)}')
            return redirect('/dashboard/?tab=form-data')

        elif action == 'edit_project':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')

            project_id = request.POST.get('project_id', '')
            project_name = request.POST.get('project_name', '').strip()
            project_type = request.POST.get('project_type', '').strip()
            status = request.POST.get('status', '').strip() or 'Not Worked'
            start_date = request.POST.get('start_date', '').strip() or None
            due_date = request.POST.get('due_date', '').strip() or None
            actual_complete_date = request.POST.get('actual_complete_date', '').strip() or None
            description = request.POST.get('description', '').strip()

            if not project_id or not project_name or not project_type:
                messages.error(request, 'Project ID, Project Name, and Project Type are required.')
            else:
                try:
                    project_service.update_project(
                        project_id=int(project_id),
                        project_name=project_name,
                        project_type=project_type,
                        status=status,
                        start_date=start_date,
                        due_date=due_date,
                        actual_complete_date=actual_complete_date,
                        description=description
                    )
                    messages.success(request, f'Project #{project_id} ("{project_name}") updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update project: {str(e)}')
            return redirect('/dashboard/?tab=add-project')

        elif action == 'employee_edit_task':
            task_id = request.POST.get('task_id', '')
            description = request.POST.get('description', '').strip()
            status = request.POST.get('status', 'Not Worked').strip()

            if not task_id:
                messages.error(request, 'Task ID is required.')
            else:
                try:
                    task_service.update_task_employee_fields(int(task_id), description, status)
                    messages.success(request, f'Task #{task_id} details updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update task: {str(e)}')
            return redirect('dashboard')



    # Fetch data based on role
    active_tab = request.GET.get('tab', 'dashboard').strip()
    context = {
        'username': username,
        'role': user_role,
        'user_id': user_id,
        'active_tab': active_tab,
    }

    # Retrieve tasks & employees lists
    all_assignable_employees = employee_service.get_users_by_role('employee')
    context['all_assignable_employees'] = all_assignable_employees

    if user_role in ('superadmin', 'admin'):
        tasks = task_service.get_all_tasks()
        projects = project_service.get_all_projects()
        context['tasks'] = tasks
        context['projects'] = projects
        context['total_tasks'] = len(tasks)
        context['total_projects'] = len(projects)
        context['not_worked_tasks'] = len([t for t in tasks if t.get('status') == 'Not Worked'])
        context['pending_tasks'] = len([t for t in tasks if t.get('status') == 'Pending'])
        context['in_progress_tasks'] = len([t for t in tasks if t.get('status') == 'In Progress'])
        context['on_hold_tasks'] = len([t for t in tasks if t.get('status') in ('On Hold', 'Hold')])
        context['completed_tasks'] = len([t for t in tasks if t.get('status') == 'Completed'])
    else:
        # Employee role
        tasks = task_service.get_tasks_by_employee(user_id, username)
        context['tasks'] = tasks
        context['total_tasks'] = len(tasks)
        context['not_worked_tasks'] = len([t for t in tasks if t.get('status') == 'Not Worked'])
        context['pending_tasks'] = len([t for t in tasks if t.get('status') == 'Pending'])
        context['in_progress_tasks'] = len([t for t in tasks if t.get('status') == 'In Progress'])
        context['on_hold_tasks'] = len([t for t in tasks if t.get('status') in ('On Hold', 'Hold')])
        context['completed_tasks'] = len([t for t in tasks if t.get('status') == 'Completed'])

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
