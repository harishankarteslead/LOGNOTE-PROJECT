import threading
import datetime
from django.db import connection
from Taskapp.services import task_request_service

_project_table_created = False
_project_table_lock = threading.Lock()


def create_project_table():
    """
    Raw SQL query to create the projects database table if it doesn't exist.
    """
    global _project_table_created
    if _project_table_created:
        return
    with _project_table_lock:
        if _project_table_created:
            return
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_name VARCHAR(255) NOT NULL,
                    project_type VARCHAR(100) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'Not Worked',
                    start_date DATE NULL,
                    due_date DATE NULL,
                    actual_complete_date DATE NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cursor.execute("SHOW COLUMNS FROM projects;")
            existing_cols = [col[0] for col in cursor.fetchall()]
            if 'status' not in existing_cols:
                cursor.execute("ALTER TABLE projects ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'Not Worked';")
            if 'actual_complete_date' not in existing_cols:
                cursor.execute("ALTER TABLE projects ADD COLUMN actual_complete_date DATE NULL;")
        _project_table_created = True


def create_project(project_name, project_type, status='Not Worked', start_date=None, due_date=None, actual_complete_date=None, description=''):
    """
    Insert a new project into the projects table.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()

    if status == 'In Progress':
        start_val = start_date if start_date else today_str
        actual_val = None
    elif status == 'Completed':
        start_val = start_date if start_date else today_str
        actual_val = actual_complete_date if actual_complete_date else today_str
    else:  # 'Not Worked', 'Pending'
        start_val = None
        actual_val = None

    due_val = due_date if due_date else None

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO projects (project_name, project_type, status, start_date, due_date, actual_complete_date, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, [project_name, project_type, status, start_val, due_val, actual_val, description])
        return cursor.lastrowid


def get_all_projects():
    """
    Retrieve all projects from database ordered by id DESC.
    """
    create_project_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, project_name, project_type, status, start_date, due_date, actual_complete_date, description, created_at
            FROM projects
            ORDER BY id DESC;
        """)
        rows = cursor.fetchall()
        projects = []
        for r in rows:
            projects.append({
                'id': r[0],
                'project_name': r[1],
                'project_type': r[2],
                'status': r[3],
                'start_date': r[4],
                'due_date': r[5],
                'actual_complete_date': r[6],
                'description': r[7],
                'created_at': r[8]
            })
        return projects


def delete_project(project_id):
    """
    Delete a project record from projects table.
    """
    create_project_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM projects
            WHERE id = %s;
        """, [project_id])
        return cursor.rowcount


def delete_projects_bulk(project_ids):
    """
    Delete multiple project records from projects table by their IDs.
    """
    if not project_ids:
        return 0
    create_project_table()
    placeholders = ', '.join(['%s'] * len(project_ids))
    with connection.cursor() as cursor:
        cursor.execute(f"""
            DELETE FROM projects
            WHERE id IN ({placeholders});
        """, list(project_ids))
        return cursor.rowcount


def cascade_project_status_to_tasks(project_name, new_status, admin_name=""):
    """
    Cascade project status changes to assigned tasks under that project:
    - If new_status is 'On Hold' / 'Hold': update all tasks under project to 'On Hold' and notify assigned employees.
    - If new_status is 'Not Worked': update all tasks under project to 'Not Worked' and notify assigned employees.
    - If new_status is 'In Progress': reset 'On Hold' tasks under project to 'Not Worked' and notify assigned employees.
    """
    if not project_name:
        return 0

    proj_clean = project_name.strip()
    status_clean = (new_status or '').strip()

    with connection.cursor() as cursor:
        if status_clean in ('On Hold', 'Hold'):
            cursor.execute("""
                SELECT id, task_name, assigned_to_id, employee_name
                FROM tasks
                WHERE LOWER(project_name) = LOWER(%s);
            """, [proj_clean])
            tasks_to_update = cursor.fetchall()

            if tasks_to_update:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'On Hold'
                    WHERE LOWER(project_name) = LOWER(%s);
                """, [proj_clean])

                notified_users = set()
                for task_id, t_name, emp_id, emp_name in tasks_to_update:
                    if emp_id and emp_id not in notified_users:
                        task_request_service.create_notification(
                            user_id=emp_id,
                            user_role='employee',
                            title='Project & Tasks On Hold',
                            message=f'Project "{proj_clean}" has been put On Hold by Admin ({admin_name or "System"}). Your assigned task(s) under this project are now On Hold.',
                            link='/dashboard/'
                        )
                        notified_users.add(emp_id)

                return len(tasks_to_update)

        elif status_clean == 'Not Worked':
            cursor.execute("""
                SELECT id, task_name, assigned_to_id, employee_name
                FROM tasks
                WHERE LOWER(project_name) = LOWER(%s);
            """, [proj_clean])
            tasks_to_update = cursor.fetchall()

            if tasks_to_update:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'Not Worked'
                    WHERE LOWER(project_name) = LOWER(%s);
                """, [proj_clean])

                notified_users = set()
                for task_id, t_name, emp_id, emp_name in tasks_to_update:
                    if emp_id and emp_id not in notified_users:
                        task_request_service.create_notification(
                            user_id=emp_id,
                            user_role='employee',
                            title='Project & Tasks Reset to Not Worked',
                            message=f'Project "{proj_clean}" status has been set to Not Worked by Admin ({admin_name or "System"}). All assigned task(s) under this project are now set to Not Worked.',
                            link='/dashboard/'
                        )
                        notified_users.add(emp_id)

                return len(tasks_to_update)

        elif status_clean == 'In Progress':
            cursor.execute("""
                SELECT id, task_name, assigned_to_id, employee_name
                FROM tasks
                WHERE LOWER(project_name) = LOWER(%s) AND status IN ('On Hold', 'Hold');
            """, [proj_clean])
            tasks_to_resume = cursor.fetchall()

            if tasks_to_resume:
                cursor.execute("""
                    UPDATE tasks
                    SET status = 'Not Worked'
                    WHERE LOWER(project_name) = LOWER(%s) AND status IN ('On Hold', 'Hold');
                """, [proj_clean])

                notified_users = set()
                for task_id, t_name, emp_id, emp_name in tasks_to_resume:
                    if emp_id and emp_id not in notified_users:
                        task_request_service.create_notification(
                            user_id=emp_id,
                            user_role='employee',
                            title='Project & Tasks Resumed',
                            message=f'Project "{proj_clean}" status has been set to In Progress by Admin ({admin_name or "System"}). Your task(s) have been reset to Not Worked so you can resume.',
                            link='/dashboard/'
                        )
                        notified_users.add(emp_id)

                return len(tasks_to_resume)

    return 0


def update_project(project_id, project_name, project_type, status='Not Worked', start_date=None, due_date=None, actual_complete_date=None, description='', admin_name=""):
    """
    Update an existing project record in the projects table and cascade status changes.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()

    with connection.cursor() as cursor:
        cursor.execute("SELECT start_date, actual_complete_date FROM projects WHERE id = %s;", [project_id])
        row = cursor.fetchone()
        existing_start = row[0].isoformat() if row and row[0] else None

    if status == 'In Progress':
        final_start = start_date if start_date else (existing_start or today_str)
        final_actual = None
    elif status == 'Completed':
        final_start = start_date if start_date else (existing_start or today_str)
        final_actual = actual_complete_date if actual_complete_date else today_str
    else:  # 'Not Worked', 'Pending', 'On Hold'
        final_start = None
        final_actual = None

    due_val = due_date if due_date else None

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE projects
            SET project_name = %s, project_type = %s, status = %s, start_date = %s, due_date = %s, actual_complete_date = %s, description = %s
            WHERE id = %s;
        """, [project_name, project_type, status, final_start, due_val, final_actual, description, project_id])
        updated_count = cursor.rowcount

    cascade_project_status_to_tasks(project_name, status, admin_name)
    return updated_count


def update_project_status(project_id, status, admin_name=""):
    """
    Update the status of a specific project and automatically cascade to tasks + notifications.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()

    with connection.cursor() as cursor:
        cursor.execute("SELECT project_name, start_date, actual_complete_date FROM projects WHERE id = %s;", [project_id])
        row = cursor.fetchone()
        if not row:
            return 0
        proj_name = row[0]
        existing_start = row[1].isoformat() if row[1] else None

    if status == 'In Progress':
        final_start = existing_start if existing_start else today_str
        final_actual = None
    elif status == 'Completed':
        final_start = existing_start if existing_start else today_str
        final_actual = today_str
    else:  # 'Not Worked', 'Pending', 'On Hold'
        final_start = None
        final_actual = None

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE projects
            SET status = %s, start_date = %s, actual_complete_date = %s
            WHERE id = %s;
        """, [status, final_start, final_actual, project_id])
        updated_count = cursor.rowcount

    cascade_project_status_to_tasks(proj_name, status, admin_name)
    return updated_count




