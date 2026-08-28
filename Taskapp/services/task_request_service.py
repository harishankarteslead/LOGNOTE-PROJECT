import threading
from django.db import connection

_tables_initialized = False
_tables_lock = threading.Lock()


def init_task_request_tables():
    """
    Ensure task_requests and notifications database tables exist.
    Also ensures missing columns like user_role are added if tables were created with an older schema.
    """
    global _tables_initialized
    if _tables_initialized:
        return
    with _tables_lock:
        if _tables_initialized:
            return
        with connection.cursor() as cursor:
            # Create task_requests table
            if connection.vendor == 'mysql':
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_requests (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        task_id INT NOT NULL,
                        task_name VARCHAR(255) NOT NULL,
                        project_name VARCHAR(255) NULL,
                        employee_id INT NOT NULL,
                        employee_name VARCHAR(150) NOT NULL,
                        reason TEXT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                        rejection_reason TEXT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL DEFAULT 0,
                        user_role VARCHAR(50) NULL,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        link VARCHAR(255) NULL,
                        is_read TINYINT(1) NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INT NOT NULL,
                        task_name VARCHAR(255) NOT NULL,
                        project_name VARCHAR(255) NULL,
                        employee_id INT NOT NULL,
                        employee_name VARCHAR(150) NOT NULL,
                        reason TEXT NULL,
                        status VARCHAR(50) NOT NULL DEFAULT 'Pending',
                        rejection_reason TEXT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INT NOT NULL DEFAULT 0,
                        user_role VARCHAR(50) NULL,
                        title VARCHAR(255) NOT NULL,
                        message TEXT NOT NULL,
                        link VARCHAR(255) NULL,
                        is_read INT NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

            # Ensure user_role and link columns exist if notifications table was created earlier with older schema
            try:
                if connection.vendor == 'mysql':
                    cursor.execute("SHOW COLUMNS FROM notifications;")
                    existing_cols = [col[0] for col in cursor.fetchall()]
                    if 'user_role' not in existing_cols:
                        cursor.execute("ALTER TABLE notifications ADD COLUMN user_role VARCHAR(50) NULL AFTER user_id;")
                    if 'link' not in existing_cols:
                        cursor.execute("ALTER TABLE notifications ADD COLUMN link VARCHAR(255) NULL AFTER message;")
                    if 'username' in existing_cols:
                        cursor.execute("ALTER TABLE notifications MODIFY COLUMN username VARCHAR(150) NULL DEFAULT '';")
                    if 'sender_name' in existing_cols:
                        cursor.execute("ALTER TABLE notifications MODIFY COLUMN sender_name VARCHAR(150) NULL DEFAULT '';")
                    if 'type' in existing_cols:
                        cursor.execute("ALTER TABLE notifications MODIFY COLUMN type VARCHAR(50) NULL DEFAULT '';")
            except Exception:
                pass

        _tables_initialized = True


def create_task_request(task_id, task_name, project_name, employee_id, employee_name, reason=""):
    """
    Create a new task request from an employee to Admin/Superadmin.
    Also creates a notification for Admins/Superadmins.
    """
    init_task_request_tables()
    emp_id = int(employee_id) if employee_id else 0
    t_id = int(task_id) if task_id else 0

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM task_requests 
            WHERE task_id = %s AND employee_id = %s AND status = 'Pending';
        """, [t_id, emp_id])
        row = cursor.fetchone()
        if row:
            req_id = row[0]
            cursor.execute("""
                UPDATE task_requests SET reason = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s;
            """, [reason, req_id])
        else:
            cursor.execute("""
                INSERT INTO task_requests (task_id, task_name, project_name, employee_id, employee_name, reason, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'Pending');
            """, [t_id, task_name, project_name or '', emp_id, employee_name, reason])
            req_id = cursor.lastrowid

    create_notification(
        user_id=0,
        user_role='all_admins',
        title='New Task Request',
        message=f'Employee {employee_name} requested permission to work on task "{task_name}" (Project: {project_name or "N/A"}).',
        link='/task-requests/'
    )
    return req_id


def get_all_task_requests():
    """
    Retrieve all task requests for Admin/Superadmin review.
    """
    init_task_request_tables()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_id, task_name, project_name, employee_id, employee_name, reason, status, rejection_reason, created_at, updated_at
            FROM task_requests
            ORDER BY id DESC;
        """)
        rows = cursor.fetchall()
        requests = []
        for r in rows:
            requests.append({
                'id': r[0],
                'task_id': r[1],
                'task_name': r[2],
                'project_name': r[3] or '',
                'employee_id': r[4],
                'employee_name': r[5],
                'reason': r[6] or '',
                'status': r[7],
                'rejection_reason': r[8] or '',
                'created_at': r[9].strftime('%Y-%m-%d %H:%M:%S') if r[9] and hasattr(r[9], 'strftime') else str(r[9] or ''),
                'updated_at': r[10].strftime('%Y-%m-%d %H:%M:%S') if r[10] and hasattr(r[10], 'strftime') else str(r[10] or '')
            })
        return requests


def get_task_requests_by_employee(employee_id):
    """
    Retrieve requests belonging to a specific employee.
    """
    init_task_request_tables()
    emp_id = int(employee_id) if employee_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_id, task_name, project_name, employee_id, employee_name, reason, status, rejection_reason, created_at, updated_at
            FROM task_requests
            WHERE employee_id = %s
            ORDER BY id DESC;
        """, [emp_id])
        rows = cursor.fetchall()
        requests = []
        for r in rows:
            requests.append({
                'id': r[0],
                'task_id': r[1],
                'task_name': r[2],
                'project_name': r[3] or '',
                'employee_id': r[4],
                'employee_name': r[5],
                'reason': r[6] or '',
                'status': r[7],
                'rejection_reason': r[8] or '',
                'created_at': r[9].strftime('%Y-%m-%d %H:%M:%S') if r[9] and hasattr(r[9], 'strftime') else str(r[9] or ''),
                'updated_at': r[10].strftime('%Y-%m-%d %H:%M:%S') if r[10] and hasattr(r[10], 'strftime') else str(r[10] or '')
            })
        return requests


def approve_task_request(request_id, admin_id=0, admin_name=""):
    """
    Approve a pending task request and notify the employee.
    """
    init_task_request_tables()
    req_id = int(request_id)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT task_id, task_name, employee_id, employee_name FROM task_requests WHERE id = %s;
        """, [req_id])
        r = cursor.fetchone()
        if not r:
            return False, "Task request not found."
        
        t_id, t_name, emp_id, emp_name = r[0], r[1], r[2], r[3]
        cursor.execute("""
            UPDATE task_requests SET status = 'Approved' WHERE id = %s;
        """, [req_id])

    create_notification(
        user_id=emp_id,
        user_role='employee',
        title='Task Request Approved!',
        message=f'Your request to work on task "{t_name}" has been APPROVED by Admin ({admin_name or "System"}).',
        link='/dashboard/'
    )
    create_notification(
        user_id=0,
        user_role='all_admins',
        title='Task Request Approved',
        message=f'Task request for employee {emp_name} (Task: "{t_name}") was APPROVED by Admin ({admin_name or "System"}).',
        link='/task-requests/'
    )
    return True, f'Task request #{req_id} approved successfully.'


def reject_task_request(request_id, rejection_reason="", admin_id=0, admin_name=""):
    """
    Reject a pending task request with a mandatory reason and notify the employee and admins.
    """
    init_task_request_tables()
    req_id = int(request_id)
    rej_reason = (rejection_reason or '').strip()
    if not rej_reason:
        return False, "Rejection reason is required."

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT task_id, task_name, employee_id, employee_name FROM task_requests WHERE id = %s;
        """, [req_id])
        r = cursor.fetchone()
        if not r:
            return False, "Task request not found."
        
        t_id, t_name, emp_id, emp_name = r[0], r[1], r[2], r[3]
        cursor.execute("""
            UPDATE task_requests SET status = 'Rejected', rejection_reason = %s WHERE id = %s;
        """, [rej_reason, req_id])

    create_notification(
        user_id=emp_id,
        user_role='employee',
        title='Task Request Rejected',
        message=f'Your request for task "{t_name}" was REJECTED by Admin ({admin_name or "System"}). Reason: {rej_reason}',
        link='/dashboard/'
    )
    create_notification(
        user_id=0,
        user_role='all_admins',
        title='Task Request Rejected',
        message=f'Task request for employee {emp_name} (Task: "{t_name}") was REJECTED by Admin ({admin_name or "System"}). Reason: {rej_reason}',
        link='/task-requests/'
    )
    return True, f'Task request #{req_id} rejected successfully.'


def get_all_notifications(user_id=0, user_role=""):
    """
    Retrieve all notifications (read and unread) for rendering full notification page.
    """
    init_task_request_tables()
    u_id = int(user_id) if user_id else 0
    role = (user_role or '').lower()

    with connection.cursor() as cursor:
        if role in ('superadmin', 'admin'):
            cursor.execute("""
                SELECT id, user_id, user_role, title, message, link, is_read, created_at
                FROM notifications
                WHERE user_id = %s OR user_role IN ('admin', 'superadmin', 'all_admins')
                ORDER BY id DESC LIMIT 100;
            """, [u_id])
        else:
            cursor.execute("""
                SELECT id, user_id, user_role, title, message, link, is_read, created_at
                FROM notifications
                WHERE user_id = %s OR (user_id = 0 AND user_role IN ('employee', 'all'))
                ORDER BY id DESC LIMIT 100;
            """, [u_id])

        rows = cursor.fetchall()
        notifications = []
        for r in rows:
            notifications.append({
                'id': r[0],
                'user_id': r[1],
                'user_role': r[2] or '',
                'title': r[3],
                'message': r[4],
                'link': r[5] or '',
                'is_read': bool(r[6]),
                'created_at': r[7].strftime('%Y-%m-%d %H:%M:%S') if r[7] and hasattr(r[7], 'strftime') else str(r[7] or '')
            })
        return notifications


def has_approved_request_for_task(employee_id, task_id):
    """
    Check if an employee has an Approved task request for a specific task.
    """
    init_task_request_tables()
    emp_id = int(employee_id) if employee_id else 0
    t_id = int(task_id) if task_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM task_requests
            WHERE employee_id = %s AND task_id = %s AND status = 'Approved';
        """, [emp_id, t_id])
        return cursor.fetchone() is not None


def create_notification(user_id=0, user_role="", title="", message="", link=""):
    """
    Insert a notification for a user or role group.
    """
    init_task_request_tables()
    u_id = int(user_id) if user_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO notifications (user_id, user_role, title, message, link, is_read)
            VALUES (%s, %s, %s, %s, %s, 0);
        """, [u_id, user_role or '', title, message, link or ''])


def get_unread_notifications(user_id=0, user_role=""):
    """
    Retrieve unread notifications for a user based on user_id or user_role.
    """
    init_task_request_tables()
    u_id = int(user_id) if user_id else 0
    role = (user_role or '').lower()

    with connection.cursor() as cursor:
        if role in ('superadmin', 'admin'):
            cursor.execute("""
                SELECT id, user_id, user_role, title, message, link, is_read, created_at
                FROM notifications
                WHERE is_read = 0 AND (user_id = %s OR user_role IN ('admin', 'superadmin', 'all_admins'))
                ORDER BY id DESC LIMIT 20;
            """, [u_id])
        else:
            cursor.execute("""
                SELECT id, user_id, user_role, title, message, link, is_read, created_at
                FROM notifications
                WHERE is_read = 0 AND (user_id = %s OR (user_id = 0 AND user_role IN ('employee', 'all')))
                ORDER BY id DESC LIMIT 20;
            """, [u_id])

        rows = cursor.fetchall()
        notifications = []
        for r in rows:
            notifications.append({
                'id': r[0],
                'user_id': r[1],
                'user_role': r[2] or '',
                'title': r[3],
                'message': r[4],
                'link': r[5] or '',
                'is_read': bool(r[6]),
                'created_at': r[7].strftime('%Y-%m-%d %H:%M:%S') if r[7] and hasattr(r[7], 'strftime') else str(r[7] or '')
            })
        return notifications


def mark_notification_read(notification_id=0, user_id=0, user_role=""):
    """
    Mark notification(s) as read.
    """
    init_task_request_tables()
    n_id = int(notification_id) if notification_id else 0
    u_id = int(user_id) if user_id else 0
    role = (user_role or '').lower()

    with connection.cursor() as cursor:
        if n_id > 0:
            cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = %s;", [n_id])
        else:
            if role in ('superadmin', 'admin'):
                cursor.execute("""
                    UPDATE notifications SET is_read = 1 
                    WHERE is_read = 0 AND (user_id = %s OR user_role IN ('admin', 'superadmin', 'all_admins'));
                """, [u_id])
            else:
                cursor.execute("""
                    UPDATE notifications SET is_read = 1 
                    WHERE is_read = 0 AND (user_id = %s OR (user_id = 0 AND user_role = 'employee'));
                """, [u_id])
        return cursor.rowcount
