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
        
        # Ensure due_date column exists if table was created earlier without it
        cursor.execute("SHOW COLUMNS FROM tasks;")
        existing_cols = [col[0] for col in cursor.fetchall()]
        if 'due_date' not in existing_cols:
            cursor.execute("ALTER TABLE tasks ADD COLUMN due_date DATE NULL;")


def create_task(task_name, description, assigned_to_id, employee_name, due_date=None, status='Pending'):
    """
    Insert a new task into the tasks table.
    """
    create_task_table()
    due_val = due_date if due_date else None
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO tasks (task_name, description, assigned_to_id, employee_name, due_date, status)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, [task_name, description, assigned_to_id, employee_name, due_val, status])
        return cursor.lastrowid


def get_all_tasks():
    """
    Retrieve all assigned tasks from the database ordered by id DESC.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at
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
                'created_at': r[7]
            })
        return tasks


def get_tasks_by_employee(assigned_to_id, employee_name=None):
    """
    Retrieve tasks assigned specifically to a given employee by ID or username.
    """
    create_task_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, task_name, description, assigned_to_id, employee_name, due_date, status, created_at
            FROM tasks
            WHERE assigned_to_id = %s OR LOWER(employee_name) = LOWER(%s)
            ORDER BY id DESC;
        """, [assigned_to_id, employee_name or ''])
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
                'created_at': r[7]
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
