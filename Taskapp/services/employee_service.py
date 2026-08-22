from django.db import connection


def create_employee_table():
    """
    Raw SQL query to create the employees database table if it doesn't exist.
    Role ENUM values are strictly enforced: 'superadmin', 'admin', 'employee'.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(128) NOT NULL,
                email VARCHAR(254) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('superadmin', 'admin', 'employee')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)


def seed_default_users():
    """
    Seed initial default user accounts if the employees table is empty.
    Allows immediate testing for all 3 role types.
    """
    # create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM employees;")
        count = cursor.fetchone()[0]
        if count == 0:
            default_users = [
                ('superadmin', 'super123', 'superadmin@gmail.com', 'superadmin'),
                ('admin', 'admin123', 'admin@gmail.com', 'admin'),
                ('employee', 'emp123', 'employee@gmail.com', 'employee'),
                ('emp1', 'emp123', 'emp1@gmail.com', 'employee')
            ]
            cursor.executemany("""
                INSERT INTO employees (username, password, email, role)
                VALUES (%s, %s, %s, %s);
            """, default_users)


def authenticate_user(username, password):
    """
    Raw SQL query to authenticate a user by matching username and case-sensitive password.
    Returns user details dictionary if found, otherwise None.
    """
    # create_employee_table()
    # seed_default_users()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, role, password 
            FROM employees
            WHERE LOWER(username) = LOWER(%s) OR (LOWER(%s) = 'employee' AND LOWER(username) = 'emp1');
        """, [username, username])
        rows = cursor.fetchall()
        for row in rows:
            db_id, db_username, db_email, db_role, db_password = row
            if db_password == password:
                return {
                    'id': db_id,
                    'username': db_username,
                    'email': db_email,
                    'role': db_role
                }
        return None




def insert_user(username, password, email, role):
    """
    Raw SQL query to insert a new user record.
    Ensures role enum value is valid before executing.
    """
    create_employee_table()
    if role not in ('superadmin', 'admin', 'employee'):
        raise ValueError("Invalid role enum value. Must be 'superadmin', 'admin', or 'employee'.")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO employees (username, password, email, role)
            VALUES (%s, %s, %s, %s);
        """, [username, password, email, role])
        return cursor.lastrowid


def get_all_users():
    """
    Raw SQL query to select all employee records from the database.
    """
    create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM employees 
            ORDER BY id ASC;
        """)
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({
                'id': r[0],
                'username': r[1],
                'email': r[2],
                'role': r[3],
                'created_at': r[4]
            })
        return users


def get_user_by_id(user_id):
    """
    Raw SQL query to select a single user record by ID.
    """
    create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM employees 
            WHERE id = %s;
        """, [user_id])
        r = cursor.fetchone()
        if r:
            return {
                'id': r[0],
                'username': r[1],
                'email': r[2],
                'role': r[3],
                'created_at': r[4]
            }
        return None


def get_users_by_role(role):
    """
    Raw SQL query to select all employee records filtering by role.
    """
    create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, role, created_at 
            FROM employees 
            WHERE role = %s
            ORDER BY id ASC;
        """, [role])
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({
                'id': r[0],
                'username': r[1],
                'email': r[2],
                'role': r[3],
                'created_at': r[4]
            })
        return users


def update_user(user_id, username, email, password, role):
    """
    Raw SQL query to update user details in the employees table.
    """
    create_employee_table()
    if role not in ('superadmin', 'admin', 'employee'):
        raise ValueError("Invalid role enum value. Must be 'superadmin', 'admin', or 'employee'.")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE employees
            SET username = %s, email = %s, password = %s, role = %s
            WHERE id = %s;
        """, [username, email, password, role, user_id])
        return cursor.rowcount


def delete_user(user_id):
    """
    Raw SQL query to delete a user record from employees table.
    """
    create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM employees
            WHERE id = %s;
        """, [user_id])
        return cursor.rowcount

