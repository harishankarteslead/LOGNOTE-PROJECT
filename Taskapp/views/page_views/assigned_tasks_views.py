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

    employee_tasks = []
    for emp in all_employees:
        emp_id = emp['id']
        emp_username = emp['username']

        emp_assigned_tasks = []
        for t in tasks:
            emp_name_str = t.get('employee_name') or ''
            emp_list = [e.strip().lower() for e in emp_name_str.split(',') if e.strip()]
            if t.get('assigned_to_id') == emp_id or emp_username.lower() in emp_list:
                emp_assigned_tasks.append(t)

        selected_task = None
        for t in emp_assigned_tasks:
            if t.get('status') == 'In Progress':
                selected_task = t
                break
        if not selected_task and emp_assigned_tasks:
            selected_task = emp_assigned_tasks[0]

        all_tasks_list = []
        for t in emp_assigned_tasks:
            due_val = t.get('due_date')
            due_str = due_val.strftime('%Y-%m-%d') if hasattr(due_val, 'strftime') else str(due_val or '-').strip()
            all_tasks_list.append({
                'id': t['id'],
                'task_name': t.get('task_name', '-'),
                'project_name': t.get('project_name', '-'),
                'description': t.get('description', '-'),
                'due_date': due_str,
                'status': t.get('status', 'Not Worked')
            })

        if selected_task:
            status_val = selected_task.get('status') or 'Not Worked'
            employee_tasks.append({
                'employee_id': emp_id,
                'employee_name': emp_username,
                'project_name': selected_task.get('project_name') or '-',
                'task_name': selected_task.get('task_name') or '-',
                'status': status_val,
                'total_tasks_count': len(emp_assigned_tasks),
                'all_tasks': all_tasks_list,
                'is_assigned': True
            })
        else:
            employee_tasks.append({
                'employee_id': emp_id,
                'employee_name': emp_username,
                'project_name': '-',
                'task_name': 'No Task Assigned',
                'status': 'Not Worked',
                'total_tasks_count': 0,
                'all_tasks': [],
                'is_assigned': False
            })

    for t in tasks:
        emp_str = t.get('employee_name') or ''
        t['emp_names_list'] = [e.strip() for e in emp_str.split(',') if e.strip()]

    in_progress_tasks_list = [t for t in tasks if t.get('status') == 'In Progress']
    in_progress_projects_list = [p for p in projects if p.get('status') == 'In Progress']
    all_assigned_tasks = tasks

    context = {
        'username': username,
        'role': user_role,
        'user_id': user_id,
        'tasks': tasks,
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
