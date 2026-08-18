from django.db import connection


def create_task_table():
    """
    Raw SQL query to create or update the tasks database table if it doesn't exist.
    Compatible with MySQL backend.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_name VARCHAR(255) NOT NULL,
                description TEXT,
                assigned_to_id INT NOT NULL,
                employee_name VARCHAR(150) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'Pending',
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


def create_task(task_name, description, assigned_to_id=0, employee_name='', due_date=None, status='Pending', project_name=None):
    """
    Insert a new task into the tasks table.
    """
    create_task_table()
    due_val = due_date if due_date else None
    proj_val = project_name if project_name else None
    emp_id_val = int(assigned_to_id) if assigned_to_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO tasks (task_name, description, assigned_to_id, employee_name, due_date, status, project_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, [task_name, description, emp_id_val, employee_name, due_val, status, proj_val])
        return cursor.lastrowid


def get_all_tasks():
    """
    Retrieve all assigned tasks from the database ordered by id DESC.
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
    Retrieve tasks assigned specifically to a given employee by ID or username.
    Supports comma-separated employee names.
    """
    create_task_table()
    emp_search = f"%{employee_name.strip()}%" if employee_name and employee_name.strip() else ""
    emp_id_val = int(assigned_to_id) if assigned_to_id else 0
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at, project_name
            FROM tasks
            WHERE (%s > 0 AND assigned_to_id = %s) OR (LOWER(%s) != '' AND LOWER(employee_name) LIKE LOWER(%s))
            ORDER BY id DESC;
        """, [emp_id_val, emp_id_val, employee_name or '', emp_search])
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


def update_task_status(task_id, status):
    """
    Update the status of a specific task.
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
    Delete a task record from the tasks table.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM tasks
            WHERE id = %s;
        """, [task_id])
        return cursor.rowcount


def update_task_details(task_id, task_name, description, assigned_to_id=0, employee_name='', due_date=None, status='Pending', project_name=None):
    """
    Update all details of a specific task.
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
    Update description and status of a task (for Employee role).
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks
            SET description = %s, status = %s
            WHERE id = %s;
        """, [description, status, task_id])
        return cursor.rowcount


