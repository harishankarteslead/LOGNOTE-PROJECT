import re
from datetime import datetime, date
from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import employee_service, task_service, project_service, task_request_service


def is_valid_email(email):
    """
    Validate email to ensure proper format and disallow multiple @ symbols or duplicate TLD extensions (.com.com).
    """
    if not email or email.count('@') != 1:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False

    parts = email.split('@')
    domain = parts[1].lower()

    domain_parts = domain.split('.')
    if len(domain_parts) > 2:
        exts = ['com', 'org', 'net', 'edu', 'gov', 'co', 'in', 'uk', 'io', 'info', 'biz']
        found_tlds = [p for p in domain_parts if p in exts]
        if len(found_tlds) > 1:
            return False

    return True


def is_past_date(date_str):
    """
    Check if a date string (YYYY-MM-DD) is earlier than today's date.
    """
    if not date_str:
        return False
    try:
        parsed_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        return parsed_date < date.today()
    except (ValueError, TypeError):
        return False


def check_task_due_date_exceeds_project(project_name, task_due_date_str):
    """
    Check if task_due_date_str is after the project's due_date (task_due_date > project_due_date).
    Returns (exceeded, project_due_date_str) tuple.
    """
    if not project_name or not task_due_date_str:
        return False, None

    projects = project_service.get_all_projects()
    matched_proj = None
    for p in projects:
        if p.get('project_name', '').strip().lower() == project_name.strip().lower():
            matched_proj = p
            break

    if not matched_proj or not matched_proj.get('due_date'):
        return False, None

    p_due = matched_proj['due_date']
    if isinstance(p_due, (datetime, date)):
        proj_due_str = p_due.strftime('%Y-%m-%d')
    else:
        proj_due_str = str(p_due).strip()

    try:
        task_date = datetime.strptime(task_due_date_str.strip(), '%Y-%m-%d').date()
        proj_date = datetime.strptime(proj_due_str, '%Y-%m-%d').date()
        if task_date > proj_date:
            return True, proj_due_str
    except (ValueError, TypeError):
        pass

    return False, proj_due_str


def check_project_is_expired(project_name):
    """
    Check if the given project's due_date has already passed (due_date < today).
    Returns (is_expired, project_due_date_str) tuple.
    """
    if not project_name:
        return False, None

    projects = project_service.get_all_projects()
    matched_proj = None
    for p in projects:
        if p.get('project_name', '').strip().lower() == project_name.strip().lower():
            matched_proj = p
            break

    if not matched_proj or not matched_proj.get('due_date'):
        return False, None

    p_due = matched_proj['due_date']
    if isinstance(p_due, (datetime, date)):
        proj_due_str = p_due.strftime('%Y-%m-%d')
    else:
        proj_due_str = str(p_due).strip()

    if is_past_date(proj_due_str):
        return True, proj_due_str

    return False, proj_due_str


def dashboard(request):
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_role or not user_id:
        messages.error(request, 'Please log in to access the dashboard.')
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        active_tab_post = request.POST.get('active_tab', '').strip()

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
            elif not re.match(r'^[a-zA-Z0-9]+$', new_username) or not re.match(r'^[a-zA-Z0-9]+$', new_password):
                messages.error(request, 'Username and Password must contain only letters (A-Z, a-z) and numbers (0-9). Special characters and spaces are not allowed.')
            elif not is_valid_email(new_email):
                messages.error(request, 'Invalid Email address format.')
            else:
                try:
                    employee_service.insert_user(new_username, new_password, new_email, role)
                    messages.success(request, f'{role.capitalize()} "{new_username}" created successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to create user: {str(e)}')
            dest_tab = active_tab_post or 'add-members'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'edit':
            target_user_id = request.POST.get('user_id', '')
            new_username = request.POST.get('username', '').strip()
            new_password = request.POST.get('password', '').strip()
            new_email = request.POST.get('email', '').strip()
            role = request.POST.get('role', 'employee').strip()

            if not target_user_id or not new_username or not new_email:
                messages.error(request, 'Username and Email are required.')
            elif not re.match(r'^[a-zA-Z0-9]+$', new_username) or (new_password and not re.match(r'^[a-zA-Z0-9]+$', new_password)):
                messages.error(request, 'Username and Password must contain only letters (A-Z, a-z) and numbers (0-9). Special characters and spaces are not allowed.')
            elif not is_valid_email(new_email):
                messages.error(request, 'Invalid Email address format.')
            else:
                try:
                    employee_service.update_user(int(target_user_id), new_username, new_email, new_password, role)
                    messages.success(request, f'User "{new_username}" updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update user: {str(e)}')
            dest_tab = active_tab_post or 'add-members'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'delete':
            target_user_id = request.POST.get('user_id', '')
            if target_user_id:
                try:
                    employee_service.delete_user(int(target_user_id))
                    messages.success(request, 'User deleted successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to delete user: {str(e)}')
            dest_tab = active_tab_post or 'add-members'
            return redirect(f'/dashboard/?tab={dest_tab}')

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

            is_proj_expired, proj_due_str = check_project_is_expired(project_name)
            exceeded, proj_due_str = check_task_due_date_exceeds_project(project_name, due_date)

            if not task_name or not assigned_to_ids:
                messages.error(request, 'Atleast One Assigned Employee is Required.')
            elif is_proj_expired:
                messages.error(
                    request,
                    f'Cannot assign task: Project "{project_name}" due date ({proj_due_str}) has expired.'
                )
            elif exceeded:
                messages.error(
                    request,
                    f'Project due date exceeded! Task Due Date ({due_date}) cannot be after Project Due Date ({proj_due_str}) for project "{project_name}".'
                )
            elif due_date and is_past_date(due_date):
                messages.error(request, 'Past dates are not allowed for Due Date.')
            else:
                try:
                    emp_ids = []
                    emp_names = []
                    for emp_id in assigned_to_ids:
                        emp = employee_service.get_user_by_id(int(emp_id))
                        if emp:
                            emp_ids.append(emp['id'])
                            emp_names.append(emp['username'])

                    if emp_names:
                        employee_names_str = ", ".join(emp_names)
                        new_task_id = task_service.create_task(
                            task_name=task_name,
                            description=description,
                            assigned_to_ids=emp_ids,
                            employee_names=emp_names,
                            due_date=due_date,
                            status=status,
                            project_name=project_name
                        )
                        messages.success(request, f'Task #{new_task_id} ("{task_name}") assigned to {employee_names_str} successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to assign task: {str(e)}')
            dest_tab = active_tab_post or 'form-data'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'update_task_status':
            task_id = request.POST.get('task_id', '') or request.POST.get('assignment_id', '')
            new_status = request.POST.get('status', '').strip()
            redirect_tab = active_tab_post or 'dashboard'
            if task_id and new_status:
                try:
                    target_task = task_service.get_task_by_id(int(task_id))
                    if target_task and new_status == 'In Progress':
                        emp_id = target_task['assigned_to_id']
                        emp_name = target_task['employee_name']
                        active_task = task_service.get_employee_in_progress_task(
                            assigned_to_id=emp_id,
                            employee_name=emp_name,
                            exclude_task_id=int(task_id)
                        )
                        if active_task:
                            messages.error(
                                request,
                                f'Employee {emp_name} already has task ("{active_task["task_name"]}") In Progress. Please set it to On Hold or Completed first.'
                            )
                            return redirect(f'/dashboard/?tab={redirect_tab}')

                    task_service.update_task_status(int(task_id), new_status)
                    messages.success(request, f'Task status updated to "{new_status}".')
                except Exception as e:
                    messages.error(request, f'Failed to update task status: {str(e)}')
            return redirect(f'/dashboard/?tab={redirect_tab}')

        elif action == 'delete_task':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            task_id = request.POST.get('task_id', '') or request.POST.get('assignment_id', '')
            if task_id:
                try:
                    task_service.delete_task(int(task_id))
                    messages.success(request, f'Task #{task_id} deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to delete task: {str(e)}')
            dest_tab = active_tab_post or 'form-data'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'bulk_delete_tasks':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            task_ids = request.POST.getlist('task_ids') or request.POST.getlist('assignment_ids')
            if task_ids:
                try:
                    deleted_count = task_service.delete_tasks_bulk([int(tid) for tid in task_ids if str(tid).isdigit()])
                    messages.success(request, f'{deleted_count} task(s) deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to bulk delete tasks: {str(e)}')
            else:
                messages.warning(request, 'No tasks were selected for deletion.')
            dest_tab = active_tab_post or 'form-data'
            return redirect(f'/dashboard/?tab={dest_tab}')

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
            elif (start_date and is_past_date(start_date)) or (due_date and is_past_date(due_date)) or (actual_complete_date and is_past_date(actual_complete_date)):
                messages.error(request, 'Past dates are not allowed in date fields.')
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
            dest_tab = active_tab_post or 'add-project'
            return redirect(f'/dashboard/?tab={dest_tab}')

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
            dest_tab = active_tab_post or 'add-project'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'bulk_delete_projects':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            project_ids = request.POST.getlist('project_ids')
            if project_ids:
                try:
                    deleted_count = project_service.delete_projects_bulk([int(pid) for pid in project_ids if str(pid).isdigit()])
                    messages.success(request, f'{deleted_count} project(s) deleted successfully.')
                except Exception as e:
                    messages.error(request, f'Failed to bulk delete projects: {str(e)}')
            else:
                messages.warning(request, 'No projects were selected for deletion.')
            dest_tab = active_tab_post or 'add-project'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'update_project_status':
            if user_role not in ('superadmin', 'admin'):
                messages.error(request, 'Permission denied.')
                return redirect('dashboard')
            project_id = request.POST.get('project_id', '')
            new_status = request.POST.get('status', '').strip()
            if project_id and new_status:
                try:
                    project_service.update_project_status(int(project_id), new_status, admin_name=username)
                    messages.success(request, f'Project #{project_id} status updated to "{new_status}".')
                except Exception as e:
                    messages.error(request, f'Failed to update project status: {str(e)}')
            dest_tab = active_tab_post or 'add-project'
            return redirect(f'/dashboard/?tab={dest_tab}')

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

            is_proj_expired, proj_due_str = check_project_is_expired(project_name)
            exceeded, proj_due_str = check_task_due_date_exceeds_project(project_name, due_date)

            if not task_id or not task_name or not assigned_to_ids:
                messages.error(request, 'Task ID, Task Name, and at least one Assigned Employee are required.')
            elif is_proj_expired:
                messages.error(
                    request,
                    f'Cannot assign task: Project "{project_name}" due date ({proj_due_str}) has expired.'
                )
            elif exceeded:
                messages.error(
                    request,
                    f'Project due date exceeded! Task Due Date ({due_date}) cannot be after Project Due Date ({proj_due_str}) for project "{project_name}".'
                )
            elif due_date and is_past_date(due_date):
                messages.error(request, 'Past dates are not allowed for Due Date.')
            else:
                try:
                    emp_ids = []
                    emp_names = []
                    for emp_id in assigned_to_ids:
                        emp = employee_service.get_user_by_id(int(emp_id))
                        if emp:
                            emp_ids.append(emp['id'])
                            emp_names.append(emp['username'])

                    if emp_names:
                        task_service.update_task_details(
                            task_id=int(task_id),
                            task_name=task_name,
                            description=description,
                            assigned_to_ids=emp_ids,
                            employee_names=emp_names,
                            due_date=due_date,
                            status=status,
                            project_name=project_name
                        )
                        messages.success(request, f'Task #{task_id} updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update task: {str(e)}')
            dest_tab = active_tab_post or 'form-data'
            return redirect(f'/dashboard/?tab={dest_tab}')

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
            elif (start_date and is_past_date(start_date)) or (due_date and is_past_date(due_date)) or (actual_complete_date and is_past_date(actual_complete_date)):
                messages.error(request, 'Past dates are not allowed in date fields.')
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
                        description=description,
                        admin_name=username
                    )
                    messages.success(request, f'Project #{project_id} ("{project_name}") updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update project: {str(e)}')
            dest_tab = active_tab_post or 'add-project'
            return redirect(f'/dashboard/?tab={dest_tab}')

        elif action == 'employee_edit_task':
            task_id = request.POST.get('task_id', '') or request.POST.get('assignment_id', '')
            status = request.POST.get('status', 'Not Worked').strip()
            dest_tab = active_tab_post or 'dashboard'

            if not task_id:
                messages.error(request, 'Task ID is required.')
            else:
                try:
                    target_task = task_service.get_task_by_id(int(task_id))
                    if target_task and status == 'In Progress':
                        active_task = task_service.get_employee_in_progress_task(
                            assigned_to_id=user_id,
                            employee_name=username,
                            exclude_task_id=int(task_id)
                        )
                        if active_task:
                            messages.error(
                                request,
                                f'Task ("{active_task["task_name"]}") is already In Progress. Please set it to On Hold or Completed before starting another task.'
                            )
                            return redirect(f'/dashboard/?tab={dest_tab}')

                    task_service.update_task_status(int(task_id), status)
                    messages.success(request, f'Task status updated successfully!')
                except Exception as e:
                    messages.error(request, f'Failed to update task: {str(e)}')
            return redirect(f'/dashboard/?tab={dest_tab}')

    # Fetch data based on role
    active_tab = request.GET.get('tab', '').strip() or request.COOKIES.get('active_tab', '').strip() or 'dashboard'
    context = {
        'username': username,
        'role': user_role,
        'user_id': user_id,
        'active_tab': active_tab,
    }

    all_assignable_employees = employee_service.get_users_by_role('employee')
    context['all_assignable_employees'] = all_assignable_employees

    if user_role in ('superadmin', 'admin'):
        tasks = task_service.get_all_tasks()
        grouped_tasks = task_service.get_grouped_tasks()
        projects = project_service.get_all_projects()

        for t in grouped_tasks:
            t_due = t.get('due_date')
            t_created = t.get('created_at')
            t['due_date_str'] = t_due.strftime('%Y-%m-%d') if hasattr(t_due, 'strftime') else (str(t_due or '-').strip())
            t['created_at_str'] = t_created.strftime('%Y-%m-%d') if hasattr(t_created, 'strftime') else (str(t_created or '-').strip())

        for t in tasks:
            t_due = t.get('due_date')
            t_created = t.get('created_at')
            t['due_date_str'] = t_due.strftime('%Y-%m-%d') if hasattr(t_due, 'strftime') else (str(t_due or '-').strip())
            t['created_at_str'] = t_created.strftime('%Y-%m-%d') if hasattr(t_created, 'strftime') else (str(t_created or '-').strip())

        for p in projects:
            p_start = p.get('start_date')
            p_due = p.get('due_date')
            p_actual = p.get('actual_complete_date')
            p_created = p.get('created_at')

            p_due_str = p_due.strftime('%Y-%m-%d') if hasattr(p_due, 'strftime') else (str(p_due or '-').strip())
            p['is_expired'] = is_past_date(p_due_str) if p_due_str and p_due_str != '-' else False
            p['start_date_str'] = p_start.strftime('%Y-%m-%d') if hasattr(p_start, 'strftime') else (str(p_start or '-').strip())
            p['due_date_str'] = p_due_str
            p['actual_complete_date_str'] = p_actual.strftime('%Y-%m-%d') if hasattr(p_actual, 'strftime') else (str(p_actual or '-').strip())
            p['created_at_str'] = p_created.strftime('%Y-%m-%d %H:%M') if hasattr(p_created, 'strftime') else (str(p_created or '-').strip())

        context['tasks'] = grouped_tasks
        context['grouped_tasks'] = grouped_tasks
        context['all_per_employee_tasks'] = tasks
        context['projects'] = projects
        context['total_tasks'] = len(grouped_tasks)
        context['total_projects'] = len(projects)
        context['not_worked_tasks'] = len([t for t in tasks if t.get('status') == 'Not Worked'])
        context['pending_tasks'] = len([t for t in tasks if t.get('status') == 'Pending'])
        context['in_progress_tasks'] = len([t for t in tasks if t.get('status') == 'In Progress'])
        context['in_progress_tasks_list'] = [t for t in tasks if t.get('status') == 'In Progress']
        context['in_progress_projects_list'] = [p for p in projects if p.get('status') == 'In Progress']
        context['on_hold_tasks'] = len([t for t in tasks if t.get('status') in ('On Hold', 'Hold')])
        context['completed_tasks'] = len([t for t in tasks if t.get('status') == 'Completed'])
    else:
        # Employee role
        tasks = task_service.get_tasks_by_employee(user_id, username)
        for t in tasks:
            t_due = t.get('due_date')
            t_created = t.get('created_at')
            t['due_date_str'] = t_due.strftime('%Y-%m-%d') if hasattr(t_due, 'strftime') else (str(t_due or '-').strip())
            t['created_at_str'] = t_created.strftime('%Y-%m-%d') if hasattr(t_created, 'strftime') else (str(t_created or '-').strip())

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

    context['all_notifications'] = task_request_service.get_all_notifications(user_id=user_id, user_role=user_role)
    context['unread_notifications'] = task_request_service.get_unread_notifications(user_id=user_id, user_role=user_role)

    response = render(request, 'dashboard.html', context)
    response.set_cookie('active_tab', active_tab, max_age=86400 * 30)
    return response
