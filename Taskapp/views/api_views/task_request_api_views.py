import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from Taskapp.services import task_request_service, task_service


@require_http_methods(["POST"])
def api_submit_task_request(request):
    """
    REST API endpoint for employees to request working on a 2nd or multiple tasks/projects.
    """
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_role = request.session.get('role')

    if not user_id or not username:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Please log in.'}, status=401)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            task_id = data.get('task_id')
            reason = (data.get('reason') or '').strip()
        else:
            task_id = request.POST.get('task_id')
            reason = (request.POST.get('reason') or '').strip()

        task_id = int(task_id) if task_id else 0
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid request data: {str(e)}'}, status=400)

    if not task_id:
        return JsonResponse({'status': 'error', 'message': 'Task ID is required.'}, status=400)

    task = task_service.get_task_by_id(task_id)
    if not task:
        return JsonResponse({'status': 'error', 'message': 'Task not found.'}, status=404)

    req_id = task_request_service.create_task_request(
        task_id=task['id'],
        task_name=task['task_name'],
        project_name=task.get('project_name', ''),
        employee_id=user_id,
        employee_name=username,
        reason=reason
    )

    return JsonResponse({
        'status': 'success',
        'message': f'Request for task "{task["task_name"]}" sent to Admin & Superadmin successfully!',
        'request_id': req_id
    })


@require_http_methods(["GET"])
def api_get_task_requests(request):
    """
    REST API endpoint to fetch task requests for Admin/Superadmin or Employee.
    """
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')

    if not user_id or not user_role:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized. Please log in.'}, status=401)

    if user_role in ('superadmin', 'admin'):
        requests = task_request_service.get_all_task_requests()
    else:
        requests = task_request_service.get_task_requests_by_employee(user_id)

    pending_count = len([r for r in requests if r['status'] == 'Pending'])

    return JsonResponse({
        'status': 'success',
        'requests': requests,
        'pending_count': pending_count
    })


@require_http_methods(["POST"])
def api_approve_task_request(request):
    """
    REST API endpoint for Admin/Superadmin to approve a task request.
    """
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_role = request.session.get('role')

    if not user_id or user_role not in ('superadmin', 'admin'):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Only Admin and Superadmin can approve requests.'}, status=403)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            request_id = data.get('request_id')
        else:
            request_id = request.POST.get('request_id')

        request_id = int(request_id) if request_id else 0
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid payload: {str(e)}'}, status=400)

    if not request_id:
        return JsonResponse({'status': 'error', 'message': 'Request ID is required.'}, status=400)

    success, msg = task_request_service.approve_task_request(
        request_id=request_id,
        admin_id=user_id,
        admin_name=username
    )

    if success:
        return JsonResponse({'status': 'success', 'message': msg})
    else:
        return JsonResponse({'status': 'error', 'message': msg}, status=400)


@require_http_methods(["POST"])
def api_reject_task_request(request):
    """
    REST API endpoint for Admin/Superadmin to reject a task request with a mandatory reason.
    """
    user_id = request.session.get('user_id')
    username = request.session.get('username')
    user_role = request.session.get('role')

    if not user_id or user_role not in ('superadmin', 'admin'):
        return JsonResponse({'status': 'error', 'message': 'Permission denied. Only Admin and Superadmin can reject requests.'}, status=403)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            request_id = data.get('request_id')
            rejection_reason = (data.get('rejection_reason') or '').strip()
        else:
            request_id = request.POST.get('request_id')
            rejection_reason = (request.POST.get('rejection_reason') or '').strip()

        request_id = int(request_id) if request_id else 0
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Invalid payload: {str(e)}'}, status=400)

    if not request_id:
        return JsonResponse({'status': 'error', 'message': 'Request ID is required.'}, status=400)

    if not rejection_reason:
        return JsonResponse({'status': 'error', 'message': 'Rejection reason is required.'}, status=400)

    success, msg = task_request_service.reject_task_request(
        request_id=request_id,
        rejection_reason=rejection_reason,
        admin_id=user_id,
        admin_name=username
    )

    if success:
        return JsonResponse({'status': 'success', 'message': msg})
    else:
        return JsonResponse({'status': 'error', 'message': msg}, status=400)


@require_http_methods(["GET"])
def api_get_notifications(request):
    """
    REST API endpoint to get unread notifications.
    """
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')

    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    notifications = task_request_service.get_unread_notifications(user_id=user_id, user_role=user_role)
    return JsonResponse({
        'status': 'success',
        'notifications': notifications,
        'unread_count': len(notifications)
    })


@require_http_methods(["POST"])
def api_mark_notifications_read(request):
    """
    REST API endpoint to mark notifications as read.
    """
    user_id = request.session.get('user_id')
    user_role = request.session.get('role')

    if not user_id:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=401)

    try:
        notification_id = 0
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            notification_id = int(data.get('notification_id') or 0)
        else:
            notification_id = int(request.POST.get('notification_id') or 0)
    except Exception:
        notification_id = 0

    count = task_request_service.mark_notification_read(notification_id=notification_id, user_id=user_id, user_role=user_role)
    return JsonResponse({
        'status': 'success',
        'message': f'Marked {count} notifications as read.'
    })
