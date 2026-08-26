from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import task_service, project_service, employee_service


def assigned_tasks_view(request):
    """
    Dedicated view for displaying assigned tasks and projects module in full-screen mode.
    Accessible by superadmin and admin roles.
    """
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_role or not user_id:
        messages.error(request, 'Please log in to access the assigned tasks module.')
        return redirect('login')

    if user_role not in ('superadmin', 'admin'):
        messages.error(request, 'Access denied. Only Superadmin and Admin can access Assigned Tasks.')
        return redirect('dashboard')

    tasks = task_service.get_all_tasks()
    projects = project_service.get_all_projects()

    all_employees = employee_service.get_users_by_role('employee')
    if not all_employees:
        all_employees = [u for u in employee_service.get_all_users() if u.get('role') == 'employee']

    in_progress_tasks_list = [t for t in tasks if t.get('status') == 'In Progress']
    in_progress_projects_list = [p for p in projects if p.get('status') == 'In Progress']
    all_assigned_tasks = in_progress_tasks_list

    employee_tasks = []
    for emp in all_employees:
        emp_id = emp['id']
        emp_username = emp['username']

        emp_in_progress_tasks = []
        for t in in_progress_tasks_list:
            emp_name_str = t.get('employee_name') or ''
            emp_list = [e.strip().lower() for e in emp_name_str.split(',') if e.strip()]
            if t.get('assigned_to_id') == emp_id or emp_username.lower() in emp_list:
                emp_in_progress_tasks.append(t)

        if emp_in_progress_tasks:
            task_names = ", ".join([t.get('task_name', '-') for t in emp_in_progress_tasks])
            proj_names = ", ".join(list(dict.fromkeys([t.get('project_name') for t in emp_in_progress_tasks if t.get('project_name')])))

            in_prog_list_formatted = []
            for t in emp_in_progress_tasks:
                due_val = t.get('due_date')
                due_str = due_val.strftime('%Y-%m-%d') if hasattr(due_val, 'strftime') else str(due_val or '-').strip()
                in_prog_list_formatted.append({
                    'id': t['id'],
                    'task_name': t.get('task_name', '-'),
                    'project_name': t.get('project_name', '-'),
                    'description': t.get('description', '-'),
                    'due_date': due_str,
                    'status': 'In Progress'
                })

            employee_tasks.append({
                'employee_id': emp_id,
                'employee_name': emp_username,
                'project_name': proj_names or '-',
                'task_name': task_names or '-',
                'status': 'In Progress',
                'total_tasks_count': len(emp_in_progress_tasks),
                'all_tasks': in_prog_list_formatted,
                'is_assigned': True
            })

    for t in tasks:
        emp_str = t.get('employee_name') or ''
        t['emp_names_list'] = [e.strip() for e in emp_str.split(',') if e.strip()]

    context = {
        'username': username,
        'role': user_role,
        'user_id': user_id,
        'tasks': in_progress_tasks_list,
        'projects': projects,
        'employee_tasks': employee_tasks,
        'in_progress_tasks_list': in_progress_tasks_list,
        'in_progress_projects_list': in_progress_projects_list,
        'all_assigned_tasks': all_assigned_tasks,
        'total_assigned_tasks': len(all_assigned_tasks),
        'total_in_progress_tasks': len(in_progress_tasks_list),
        'total_in_progress_projects': len(in_progress_projects_list),
    }

    return render(request, 'assigned_tasks.html', context)
