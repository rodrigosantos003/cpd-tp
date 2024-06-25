"""
Auxiliary functions
"""
import sqlite3


def get_valid_user(db, auth):
    """
    Checks if the given credentials are valid and returns its user
    :param db: Database object
    :param auth: Request authorization header
    :return: User if the credentials are valid, null otherwise
    """
    if not auth:
        return None

    try:
        user = db.execute_query(f'SELECT * FROM user WHERE username=? AND password=?', (
            auth.username,
            auth.password,
        )).fetchone()
    except (sqlite3.Error, Exception):
        return None

    if not user:
        return None

    return user


def get_required_fields(request_form, required_fields):
    """
    Returns the required fields from the request
    :param request_form: Request form object
    :param required_fields: List of required fields
    :return: List of required fields if all are present, error message otherwise
    """
    missing_fields = [field for field in required_fields if not request_form.get(field)]
    if missing_fields:
        return None

    values = [request_form.get(field) for field in required_fields]
    return values


def is_user_project(db, project_id, user_id):
    try:
        project = db.execute_query(stmt='SELECT id, user_id FROM project WHERE id=?', args=(project_id,)).fetchone()
        if project['user_id'] == user_id:
            return True

        return False

    except (sqlite3.Error, Exception):
        return False


def is_project_collaborator(db, project_id, user_id):
    try:
        collaborator = db.execute_query(stmt='SELECT * FROM collaborator WHERE project_id=? AND user_id=?',
                                        args=(project_id, user_id)).fetchone()
        if collaborator:
            return True

        return False

    except (sqlite3.Error, Exception):
        return False


def is_task_manager(db, task_id, user_id):
    try:
        task = db.execute_query(stmt='SELECT * FROM task WHERE id=?', args=(task_id,)).fetchone()
        if task['manager_id'] == user_id:
            return True

        return False

    except (sqlite3.Error, Exception):
        return False
