from django.shortcuts import render, redirect
from django.contrib import messages
from Taskapp.services import task_service, project_service


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
        'in_progress_tasks_list': in_progress_tasks_list,
        'in_progress_projects_list': in_progress_projects_list,
        'all_assigned_tasks': all_assigned_tasks,
        'total_assigned_tasks': len(all_assigned_tasks),
        'total_in_progress_tasks': len(in_progress_tasks_list),
        'total_in_progress_projects': len(in_progress_projects_list),
    }

    return render(request, 'assigned_tasks.html', context)
