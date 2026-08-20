import datetime
from django.db import connection


def create_project_table():
    """
    Raw SQL query to create the projects database table if it doesn't exist.
    """
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


def create_project(project_name, project_type, status='Not Worked', start_date=None, due_date=None, actual_complete_date=None, description=''):
    """
    Insert a new project into the projects table.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()
    if status == 'In Progress' and not start_date:
        start_date = today_str
    if status == 'Completed' and not actual_complete_date:
        actual_complete_date = today_str

    start_val = start_date if start_date else None
    due_val = due_date if due_date else None
    actual_val = actual_complete_date if actual_complete_date else None

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


def update_project(project_id, project_name, project_type, status='Not Worked', start_date=None, due_date=None, actual_complete_date=None, description=''):
    """
    Update an existing project record in the projects table.
    Preserves start_date and actual_complete_date if they already exist in database or if status changes.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()

    with connection.cursor() as cursor:
        cursor.execute("SELECT start_date, actual_complete_date FROM projects WHERE id = %s;", [project_id])
        row = cursor.fetchone()
        existing_start = row[0].isoformat() if row and row[0] else None
        existing_actual = row[1].isoformat() if row and row[1] else None

    final_start = start_date if start_date else existing_start
    if (status in ('In Progress', 'Completed')) and not final_start:
        final_start = today_str

    final_actual = actual_complete_date if actual_complete_date else existing_actual
    if status == 'Completed' and not final_actual:
        final_actual = today_str

    due_val = due_date if due_date else None

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE projects
            SET project_name = %s, project_type = %s, status = %s, start_date = %s, due_date = %s, actual_complete_date = %s, description = %s
            WHERE id = %s;
        """, [project_name, project_type, status, final_start, due_val, final_actual, description, project_id])
        return cursor.rowcount


def update_project_status(project_id, status):
    """
    Update the status of a specific project and automatically handle start_date / actual_complete_date.
    """
    create_project_table()
    today_str = datetime.date.today().isoformat()

    with connection.cursor() as cursor:
        cursor.execute("SELECT start_date, actual_complete_date FROM projects WHERE id = %s;", [project_id])
        row = cursor.fetchone()
        existing_start = row[0].isoformat() if row and row[0] else None
        existing_actual = row[1].isoformat() if row and row[1] else None

    final_start = existing_start
    if (status in ('In Progress', 'Completed')) and not final_start:
        final_start = today_str

    final_actual = existing_actual
    if status == 'Completed' and not final_actual:
        final_actual = today_str

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE projects
            SET status = %s, start_date = %s, actual_complete_date = %s
            WHERE id = %s;
        """, [status, final_start, final_actual, project_id])
        return cursor.rowcount



