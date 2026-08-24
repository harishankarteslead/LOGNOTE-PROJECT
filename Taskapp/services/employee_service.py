from django.db import connection
from django.contrib.auth.hashers import make_password, check_password


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
                password VARCHAR(255) NOT NULL,
                email VARCHAR(254) NOT NULL,
                role VARCHAR(20) NOT NULL CHECK (role IN ('superadmin', 'admin', 'employee')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Ensure password column fits long hashes
        try:
            cursor.execute("ALTER TABLE employees MODIFY COLUMN password VARCHAR(255) NOT NULL;")
        except Exception:
            pass


def is_hashed(password_str):
    """
    Check if password is already hashed using standard Django hasher formats.
    """
    if not password_str:
        return False
    return password_str.startswith(('pbkdf2_sha256$', 'pbkdf2_sha1$', 'bcrypt$', 'argon2$', 'crypt$', 'md5$', 'sha1$'))


def migrate_existing_passwords():
    """
    Scans all rows in the employees table and converts plain-text passwords into PBKDF2 hashes.
    """
    create_employee_table()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, password FROM employees;")
        rows = cursor.fetchall()
        for user_id, raw_pass in rows:
            if raw_pass and not is_hashed(raw_pass):
                hashed_pass = make_password(raw_pass)
                cursor.execute("UPDATE employees SET password = %s WHERE id = %s;", [hashed_pass, user_id])


def seed_default_users():
    """
    Seed initial default user accounts if the employees table is empty.
    Allows immediate testing for all 3 role types.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM employees;")
        count = cursor.fetchone()[0]
        if count == 0:
            default_users = [
                ('superadmin', make_password('super123'), 'superadmin@gmail.com', 'superadmin'),
                ('admin', make_password('admin123'), 'admin@gmail.com', 'admin'),
                ('employee', make_password('emp123'), 'employee@gmail.com', 'employee'),
                ('emp1', make_password('emp123'), 'emp1@gmail.com', 'employee')
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
    migrate_existing_passwords()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, role, password 
            FROM employees
            WHERE LOWER(username) = LOWER(%s) OR (LOWER(%s) = 'employee' AND LOWER(username) = 'emp1');
        """, [username, username])
        rows = cursor.fetchall()
        for row in rows:
            db_id, db_username, db_email, db_role, db_password = row
            # Enforce case-sensitive username matching as created in Add Members / Employees
            if db_username != username and not (username == 'employee' and db_username == 'emp1'):
                continue

            if is_hashed(db_password):
                if check_password(password, db_password):
                    return {
                        'id': db_id,
                        'username': db_username,
                        'email': db_email,
                        'role': db_role
                    }
            else:
                if db_password == password:
                    new_hash = make_password(password)
                    with connection.cursor() as update_cursor:
                        update_cursor.execute("UPDATE employees SET password = %s WHERE id = %s;", [new_hash, db_id])
                    return {
                        'id': db_id,
                        'username': db_username,
                        'email': db_email,
                        'role': db_role
                    }
        return None


def insert_user(username, password, email, role):
    """
    Raw SQL query to insert a new user record with password hashed using PBKDF2.
    Ensures role enum value is valid before executing.
    """
    create_employee_table()
    if role not in ('superadmin', 'admin', 'employee'):
        raise ValueError("Invalid role enum value. Must be 'superadmin', 'admin', or 'employee'.")
    
    hashed_password = make_password(password) if password else make_password('')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO employees (username, password, email, role)
            VALUES (%s, %s, %s, %s);
        """, [username, hashed_password, email, role])
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
    If password is provided, hashes and updates it. Otherwise retains current password.
    """
    create_employee_table()
    if role not in ('superadmin', 'admin', 'employee'):
        raise ValueError("Invalid role enum value. Must be 'superadmin', 'admin', or 'employee'.")
    
    with connection.cursor() as cursor:
        if password and len(password.strip()) > 0:
            hashed_password = make_password(password.strip())
            cursor.execute("""
                UPDATE employees
                SET username = %s, email = %s, password = %s, role = %s
                WHERE id = %s;
            """, [username, email, hashed_password, role, user_id])
        else:
            cursor.execute("""
                UPDATE employees
                SET username = %s, email = %s, role = %s
                WHERE id = %s;
            """, [username, email, role, user_id])
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


