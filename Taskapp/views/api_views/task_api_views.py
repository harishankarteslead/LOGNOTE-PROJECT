import json
from datetime import datetime, date
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Taskapp.services import task_service, employee_service, project_service
from Taskapp.views.page_views.dashboard_views import (
    is_past_date,
    check_project_is_expired,
    check_task_due_date_exceeds_project
)


def format_date(val):
    if not val:
        return ''
    if isinstance(val, (datetime, date)):
        return val.strftime('%Y-%m-%d')
    return str(val).strip() 


@require_http_methods(["GET"])
def api_get_tasks(request):
    """
    REST API endpoint to fetch current tasks and summary statistics.
    Returns JSON feed for live monitoring without page reloads.
    """
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_role or not user_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Please log in.'}, status=401)

    if user_role in ('superadmin', 'admin'):
        tasks = task_service.get_all_tasks()
        projects = project_service.get_all_projects()
    else:
        tasks = task_service.get_tasks_by_employee(user_id, username)
        projects = []

    # Format dates and structure output
    formatted_tasks = []
    for t in tasks:
        due_str = format_date(t.get('due_date'))
        created_str = format_date(t.get('created_at'))
        emp_name = t.get('employee_name') or ''
        emp_list = [e.strip() for e in emp_name.split(',') if e.strip()]

        formatted_tasks.append({
            'id': t['id'],
            'task_name': t.get('task_name', ''),
            'description': t.get('description', ''),
            'assigned_to_id': t.get('assigned_to_id', 0),
            'employee_name': emp_name,
            'emp_names_list': emp_list,
            'status': t.get('status', 'Not Worked'),
            'due_date': due_str,
            'created_at': created_str,
            'project_name': t.get('project_name') or ''
        })

    # Summary metrics
    not_worked_count = len([t for t in formatted_tasks if t['status'] == 'Not Worked'])
    pending_count = len([t for t in formatted_tasks if t['status'] == 'Pending'])
    in_progress_count = len([t for t in formatted_tasks if t['status'] == 'In Progress'])
    on_hold_count = len([t for t in formatted_tasks if t['status'] in ('On Hold', 'Hold')])
    completed_count = len([t for t in formatted_tasks if t['status'] == 'Completed'])

    in_progress_tasks_list = [t for t in formatted_tasks if t['status'] == 'In Progress']

    # Build per-employee task status list (all employees)
    all_employees = employee_service.get_users_by_role('employee')
    if not all_employees:
        all_employees = [u for u in employee_service.get_all_users() if u.get('role') == 'employee']

    all_tasks = task_service.get_all_tasks()
    employee_tasks = []
    for emp in all_employees:
        emp_id = emp['id']
        emp_username = emp['username']

        emp_assigned_tasks = []
        for t in all_tasks:
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
            due_str = format_date(t.get('due_date'))
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

    return JsonResponse({
        'status': 'success',
        'role': user_role,
        'username': username,
        'user_id': user_id,
        'total_tasks': len(formatted_tasks),
        'not_worked_tasks': not_worked_count,
        'pending_tasks': pending_count,
        'in_progress_tasks': in_progress_count,
        'on_hold_tasks': on_hold_count,
        'completed_tasks': completed_count,
        'tasks': formatted_tasks,
        'in_progress_tasks_list': in_progress_tasks_list,
        'employee_tasks': employee_tasks
    })


@require_http_methods(["POST"])
def api_update_task_status(request):
    """
    REST API endpoint for employees, admins, and superadmins to update task status without page refresh.
    Enforces validation rule: An employee cannot have multiple tasks set to 'In Progress' concurrently.
    """
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    if not user_role or not user_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Please log in.'}, status=401)

    try:
        if request.content_type == 'application/json':
            body_data = json.loads(request.body)
            task_id = body_data.get('task_id') or body_data.get('assignment_id')
            new_status = (body_data.get('status') or '').strip()
        else:
            task_id = request.POST.get('task_id') or request.POST.get('assignment_id')
            new_status = (request.POST.get('status') or '').strip()
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid payload: {str(e)}'}, status=400)

    if not task_id or not new_status:
        return JsonResponse({'status': 'error', 'message': 'Task ID and Status are required.'}, status=400)

    try:
        task_id_int = int(task_id)
        target_task = task_service.get_task_by_id(task_id_int)
        if not target_task:
            return JsonResponse({'status': 'error', 'message': 'Task not found.'}, status=404)

        # Check permissions: employee can only update their assigned task
        if user_role == 'employee':
            emp_id = target_task.get('assigned_to_id')
            emp_name = target_task.get('employee_name')
            if emp_id != user_id and username not in emp_name:
                return JsonResponse({'status': 'error', 'message': 'Permission denied. You can only update your own tasks.'}, status=403)

        # Enforce single 'In Progress' task rule for the assigned employee
        if new_status == 'In Progress':
            target_emp_id = target_task.get('assigned_to_id') or user_id
            target_emp_name = target_task.get('employee_name') or username
            active_task = task_service.get_employee_in_progress_task(
                assigned_to_id=target_emp_id,
                employee_name=target_emp_name,
                exclude_task_id=task_id_int
            )
            if active_task:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Employee {target_emp_name} already has task ("{active_task["task_name"]}") In Progress. Please set it to On Hold or Completed first.'
                }, status=400)

        task_service.update_task_status(task_id_int, new_status)
        return JsonResponse({
            'status': 'success',
            'message': f'Task status updated to "{new_status}" successfully.',
            'task_id': task_id_int,
            'new_status': new_status
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to update status: {str(e)}'}, status=500)


@require_http_methods(["POST"])
def api_assign_task(request):
    """
    REST API endpoint for Superadmin and Admin to assign tasks without page refresh.
    """
    user_role = request.session.get('role')
    user_id = request.session.get('user_id')

    if not user_role or not user_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Please log in.'}, status=401)

    if user_role not in ('superadmin', 'admin'):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Only Admin and Superadmin can assign tasks.'}, status=403)

    try:
        if request.content_type == 'application/json':
            body_data = json.loads(request.body)
            task_name = (body_data.get('task_name') or '').strip()
            project_name = (body_data.get('project_name') or '').strip()
            description = (body_data.get('description') or '').strip()
            assigned_to_ids = body_data.get('assigned_to_ids') or []
            due_date = (body_data.get('due_date') or '').strip() or None
            status = (body_data.get('status') or '').strip() or 'Not Worked'
        else:
            task_name = (request.POST.get('task_name') or '').strip()
            project_name = (request.POST.get('project_name') or '').strip()
            description = (request.POST.get('description') or '').strip()
            assigned_to_ids = request.POST.getlist('assigned_to_ids')
            due_date = (request.POST.get('due_date') or '').strip() or None
            status = (request.POST.get('status') or '').strip() or 'Not Worked'

        if isinstance(assigned_to_ids, (int, str)):
            assigned_to_ids = [assigned_to_ids]
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid payload: {str(e)}'}, status=400)

    if not task_name or not assigned_to_ids:
        return JsonResponse({'status': 'error', 'message': 'Task Name and at least one Assigned Employee are required.'}, status=400)

    is_proj_expired, proj_due_str = check_project_is_expired(project_name)
    exceeded, proj_due_str = check_task_due_date_exceeds_project(project_name, due_date)

    if is_proj_expired:
        return JsonResponse({
            'status': 'error',
            'message': f'Cannot assign task: Project "{project_name}" due date ({proj_due_str}) has expired.'
        }, status=400)

    if exceeded:
        return JsonResponse({
            'status': 'error',
            'message': f'Project due date exceeded! Task Due Date ({due_date}) cannot be after Project Due Date ({proj_due_str}) for project "{project_name}".'
        }, status=400)

    if due_date and is_past_date(due_date):
        return JsonResponse({'status': 'error', 'message': 'Past dates are not allowed for Due Date.'}, status=400)

    try:
        emp_ids = []
        emp_names = []
        for emp_id in assigned_to_ids:
            emp = employee_service.get_user_by_id(int(emp_id))
            if emp:
                emp_ids.append(emp['id'])
                emp_names.append(emp['username'])

        if not emp_names:
            return JsonResponse({'status': 'error', 'message': 'Selected employee(s) invalid.'}, status=400)

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

        return JsonResponse({
            'status': 'success',
            'message': f'Task #{new_task_id} ("{task_name}") assigned to {employee_names_str} successfully!',
            'task_id': new_task_id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to assign task: {str(e)}'}, status=500)
