import threading
from django.db import connection

_task_table_created = False
_task_table_lock = threading.Lock()


def create_task_table():
    """
    Raw SQL query to create or update the tasks database table.
    Compatible with MySQL and SQLite backends.
    """
    global _task_table_created
    if _task_table_created:
        return
    with _task_table_lock:
        if _task_table_created:
            return
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    task_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    assigned_to_id INT NOT NULL DEFAULT 0,
                    employee_name VARCHAR(150) NOT NULL DEFAULT '',
                    status VARCHAR(50) NOT NULL DEFAULT 'Not Worked',
                    due_date DATE NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Ensure due_date & project_name columns exist if table was created earlier without them
            cursor.execute("SHOW COLUMNS FROM tasks;")
            existing_cols = [col[0] for col in cursor.fetchall()]
            if 'due_date' not in existing_cols:
                cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATE NULL;")
            if 'project_name' not in existing_cols:
                cursor.execute("ALTER TABLE tasks ADD COLUMN project_name VARCHAR(255) NULL;")

            # Drop task_assignments table if it exists to keep database clean
            try:
                cursor.execute("DROP TABLE IF EXISTS task_assignments;")
            except Exception:
                pass

        deduplicate_existing_tasks()
        _task_table_created = True


def deduplicate_existing_tasks():
    """
    Remove duplicate task rows with identical task_name, assigned_to_id, employee_name, and project_name.
    Keeps the record with the smaller ID.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE t1 FROM tasks t1
                INNER JOIN tasks t2 
                ON t1.task_name = t2.task_name 
               AND t1.assigned_to_id = t2.assigned_to_id
               AND LOWER(t1.employee_name) = LOWER(t2.employee_name)
               AND COALESCE(t1.project_name, '') = COALESCE(t2.project_name, '')
               AND t1.id > t2.id;
            """)
    except Exception:
        pass


def create_task(task_name, description, assigned_to_ids=None, employee_names=None, due_date=None, status='Not Worked', project_name=None):
    """
    Insert task records directly into the tasks table.
    If assigned to multiple employees, creates a separate row in tasks table for each employee.
    """
    create_task_table()
    due_val = due_date if due_date else None
    proj_val = project_name if project_name else None

    # Handle assigned_to_ids argument
    if isinstance(assigned_to_ids, (int, str)):
        assigned_to_ids = [assigned_to_ids] if str(assigned_to_ids).isdigit() else []
    assigned_to_ids = [int(i) for i in (assigned_to_ids or []) if str(i).isdigit()]

    # Handle employee_names argument
    if isinstance(employee_names, str):
        employee_names = [n.strip() for n in employee_names.split(',') if n.strip()]
    employee_names = employee_names or []

    created_task_ids = []
    with connection.cursor() as cursor:
        if employee_names:
            for idx, emp_name in enumerate(employee_names):
                emp_id = assigned_to_ids[idx] if idx < len(assigned_to_ids) else 0

                # Check if identical task record was already created recently to prevent duplicate insertion
                cursor.execute("""
                    SELECT id FROM tasks 
                    WHERE task_name = %s AND assigned_to_id = %s AND LOWER(employee_name) = LOWER(%s)
                      AND COALESCE(project_name, '') = COALESCE(%s, '')
                    LIMIT 1;
                """, [task_name, emp_id, emp_name, proj_val or ''])
                existing_row = cursor.fetchone()
                if existing_row:
                    created_task_ids.append(existing_row[0])
                    continue

                cursor.execute("""
                    INSERT INTO tasks (task_name, description, assigned_to_id, employee_name, due_date, status, project_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, [task_name, description, emp_id, emp_name, due_val, status, proj_val])
                created_task_ids.append(cursor.lastrowid)
        else:
            primary_emp_id = assigned_to_ids[0] if assigned_to_ids else 0

            cursor.execute("""
                SELECT id FROM tasks 
                WHERE task_name = %s AND assigned_to_id = %s AND LOWER(employee_name) = ''
                  AND COALESCE(project_name, '') = COALESCE(%s, '')
                LIMIT 1;
            """, [task_name, primary_emp_id, proj_val or ''])
            existing_row = cursor.fetchone()
            if existing_row:
                created_task_ids.append(existing_row[0])
            else:
                cursor.execute("""
                    INSERT INTO tasks (task_name, description, assigned_to_id, employee_name, due_date, status, project_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, [task_name, description, primary_emp_id, '', due_val, status, proj_val])
                created_task_ids.append(cursor.lastrowid)

    return created_task_ids[0] if created_task_ids else None


def get_all_tasks():
    """
    Retrieve all assigned tasks from the tasks table ordered by id DESC.
    Each row represents a specific task assigned to an employee with their individual status.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at, project_name
            FROM tasks
            ORDER BY id DESC;
        """)
        rows = cursor.fetchall()
        tasks = []
        for r in rows:
            tasks.append({
                'id': r[0],
                'task_name': r[1],
                'description': r[2],
                'assigned_to_id': r[3],
                'employee_name': r[4],
                'due_date': r[5],
                'status': r[6],
                'created_at': r[7],
                'project_name': r[8] if len(r) > 8 else None
            })
        return tasks


def get_tasks_by_employee(assigned_to_id=0, employee_name=None):
    """
    Retrieve tasks assigned specifically to a given employee by ID or username from the tasks table.
    """
    create_task_table()
    emp_id_val = int(assigned_to_id) if assigned_to_id else 0
    emp_name_clean = (employee_name or '').strip().lower()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at, project_name
            FROM tasks
            ORDER BY id DESC;
        """)
        rows = cursor.fetchall()
        tasks = []
        for r in rows:
            t_emp_id = r[3]
            t_emp_str = (r[4] or '').lower()
            emp_list = [e.strip().lower() for e in t_emp_str.split(',') if e.strip()]

            if (emp_id_val > 0 and t_emp_id == emp_id_val) or (emp_name_clean and emp_name_clean in emp_list):
                tasks.append({
                    'id': r[0],
                    'task_name': r[1],
                    'description': r[2],
                    'assigned_to_id': r[3],
                    'employee_name': r[4],
                    'due_date': r[5],
                    'status': r[6],
                    'created_at': r[7],
                    'project_name': r[8] if len(r) > 8 else None
                })
        return tasks


def update_task_status(task_id, status):
    """
    Update status of a specific task row in the tasks table.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET status = %s
            WHERE id = %s;
        """, [status, task_id])
        return cursor.rowcount


def delete_task(task_id):
    """
    Delete a task record from the tasks table by ID.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s;", [task_id])
        return cursor.rowcount


def delete_tasks_bulk(task_ids):
    """
    Delete multiple task records from the tasks table by their IDs.
    """
    if not task_ids:
        return 0
    create_task_table()
    placeholders = ', '.join(['%s'] * len(task_ids))
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM tasks WHERE id IN ({placeholders});", list(task_ids))
        return cursor.rowcount


def update_task_details(task_id, task_name, description, assigned_to_id=0, employee_name='', due_date=None, status='Not Worked', project_name=None):
    """
    Update all details of a specific task row in the tasks table.
    """
    create_task_table()
    due_val = due_date if due_date else None
    proj_val = project_name if project_name else None
    emp_id_val = int(assigned_to_id) if assigned_to_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET task_name = %s, description = %s, assigned_to_id = %s, employee_name = %s, due_date = %s, status = %s, project_name = %s
            WHERE id = %s;
        """, [task_name, description, emp_id_val, employee_name, due_val, status, proj_val, task_id])
        return cursor.rowcount


def update_task_employee_fields(task_id, description, status):
    """
    Update description and status of a task for employee role.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET status = %s, description = %s
            WHERE id = %s;
        """, [status, description, task_id])
        return cursor.rowcount


def get_task_by_id(task_id):
    """
    Retrieve a specific task by ID from the tasks table.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at, project_name
            FROM tasks
            WHERE id = %s;
        """, [task_id])
        r = cursor.fetchone()
        if r:
            return {
                'id': r[0],
                'task_name': r[1],
                'description': r[2],
                'assigned_to_id': r[3],
                'employee_name': r[4],
                'due_date': r[5],
                'status': r[6],
                'created_at': r[7],
                'project_name': r[8] if len(r) > 8 else None
            }
        return None


def get_employee_in_progress_task(assigned_to_id=0, employee_name=None, exclude_task_id=None):
    """
    Check if an employee currently has an 'In Progress' task in the tasks table.
    Returns the active task dict if found, or None.
    """
    create_task_table()
    emp_search = f"%{employee_name.strip()}%" if employee_name and employee_name.strip() else ""
    emp_id_val = int(assigned_to_id) if assigned_to_id else 0
    ex_id_val = int(exclude_task_id) if exclude_task_id else 0

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at, project_name
            FROM tasks
            WHERE status = 'In Progress'
              AND (%s = 0 OR id != %s)
              AND ((%s > 0 AND assigned_to_id = %s) OR (LOWER(%s) != '' AND LOWER(employee_name) LIKE LOWER(%s)))
            LIMIT 1;
        """, [ex_id_val, ex_id_val, emp_id_val, emp_id_val, employee_name or '', emp_search])
        r = cursor.fetchone()
        if r:
            return {
                'id': r[0],
                'task_name': r[1],
                'description': r[2],
                'assigned_to_id': r[3],
                'employee_name': r[4],
                'due_date': r[5],
                'status': r[6],
                'created_at': r[7],
                'project_name': r[8] if len(r) > 8 else None
            }
        return None

