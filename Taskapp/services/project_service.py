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
                start_date DATE NULL,
                due_date DATE NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def create_project(project_name, project_type, start_date=None, due_date=None, description=''):
    """
    Insert a new project into the projects table.
    """
    create_project_table()
    start_val = start_date if start_date else None
    due_val = due_date if due_date else None
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO projects (project_name, project_type, start_date, due_date, description)
            VALUES (%s, %s, %s, %s, %s);
        """, [project_name, project_type, start_val, due_val, description])
        return cursor.lastrowid


def get_all_projects():
    """
    Retrieve all projects from database ordered by id DESC.
    """
    create_project_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, project_name, project_type, start_date, due_date, description, created_at
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
                'start_date': r[3],
                'due_date': r[4],
                'description': r[5],
                'created_at': r[6]
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


def update_project(project_id, project_name, project_type, start_date=None, due_date=None, description=''):
    """
    Update an existing project record in the projects table.
    """
    create_project_table()
    start_val = start_date if start_date else None
    due_val = due_date if due_date else None
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE projects
            SET project_name = %s, project_type = %s, start_date = %s, due_date = %s, description = %s
            WHERE id = %s;
        """, [project_name, project_type, start_val, due_val, description, project_id])
        return cursor.rowcount

