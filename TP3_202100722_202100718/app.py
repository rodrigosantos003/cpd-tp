"""
 Flask REST application

"""
import sqlite3

from datetime import date
from flask import Flask, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from models import Database
from utils import get_valid_user, get_required_fields, is_user_project, is_project_collaborator, is_task_manager

# ==========
#  Settings
# ==========

app = Flask(__name__)
app.config['STATIC_URL_PATH'] = '/static'
app.config['DEBUG'] = True
bcrypt = Bcrypt(app)

# ==========
#  Database
# ==========

# Creates a sqlite database in memory
db = Database(filename=':memory:', schema='schema.sql')
db.recreate()


# ===========
#  Web views
# ===========

@app.route('/')
def index():
    """
    Index page
    :return:
    """
    return app.send_static_file('index.html')


# ===========
#  API views
# ===========

@app.route('/api/user/register/', methods=['POST'])
def user_register():
    """
    Registers a new user.
    Does not require authorization.

    """
    # Get data
    fields = get_required_fields(request.form, ['name', 'email', 'username', 'password'])
    if fields is None:
        return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

    # Create user on database and send response
    try:
        hashed_password = bcrypt.generate_password_hash(fields[3]).decode('utf-8')

        user_id = db.execute_update(
            stmt='INSERT INTO user VALUES(null, ?, ?, ?, ?)',
            args=(fields[0], fields[1], fields[2], hashed_password)
        )

        return make_response(jsonify({'message': 'User registered successfully', 'user': {
            'id': user_id,
            'name': fields[0],
            'email': fields[1],
            'username': fields[2],
            'password': hashed_password
        }}), 201)
    except (sqlite3.Error, Exception) as e:
        app.logger.error('%s', str(e))
        return make_response(jsonify({'message': 'Error: Failed to register user'}), 500)


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    # Returns user data
    if request.method == 'GET':
        return make_response(jsonify({'user': user}), 200)
    # Updates user data
    else:
        fields = get_required_fields(request.form, ['name', 'email', 'username', 'password'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        # Update user on database
        try:
            db.execute_query(
                stmt='UPDATE user SET name=?, email=?, username=?, password=? WHERE id=?',
                args=(fields[0], fields[1], fields[2], fields[3], user['id'])
            )

            return make_response(jsonify({'message': 'User updated successfully', 'user': {
                'id': user['id'],
                'name': fields[0],
                'email': fields[1],
                'username': fields[2],
                'password': fields[3]
            }}), 200)
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error: Failed to update user'}), 500)


@app.route('/api/projects/', methods=['GET', 'POST'])
def project_list():
    """
    Project list.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    if request.method == 'GET':
        # Returns the list of projects of the user or where the user is a collaborator
        projects = db.execute_query(
            stmt='''
            SELECT *, 'owner' as role FROM project 
            WHERE user_id=? 
            UNION 
            SELECT project.*, 'collaborator' as role FROM project 
            JOIN collaborator ON project.id = collaborator.project_id 
            WHERE collaborator.user_id=?
            ''',
            args=(user['id'], user['id'])
        ).fetchall()

        return make_response(jsonify({"projects": projects}))
    else:
        # Adds a project to the list
        fields = get_required_fields(request.form, ['title'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            current_date = date.today().strftime('%Y-%m-%d')
            project_id = db.execute_update(
                stmt='INSERT INTO project VALUES (null, ?, ?, ?, ?)',
                args=(user['id'], fields[0], current_date, current_date)
            )

            return make_response(jsonify({'message': 'Project added successfully', 'project': {
                'id': project_id,
                'user_id': user['id'],
                'title': fields[0],
                'creation_date': current_date,
                'last_update': current_date
            }}), 201)
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error adding project'}), 500)


@app.route('/api/projects/<int:pk>/', methods=['GET', 'PUT', 'DELETE'])
def project_detail(pk):
    """
    Project detail.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    if not ((request.method == 'GET' and is_project_collaborator(db, pk, user['id'])) or
            is_user_project(db, pk, user['id'])):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user or the user is not a '
                                'collaborator'}),
            403)

    if request.method == 'GET':
        # Returns a project
        project = db.execute_query(
            stmt='SELECT * FROM project WHERE id=?',
            args=(pk,)
        ).fetchone()
        return make_response(jsonify({'project': project}))

    elif request.method == 'PUT':
        # Updates a project
        project = db.execute_query(
            stmt='SELECT * FROM project WHERE id=?',
            args=(pk,)
        ).fetchone()

        fields = get_required_fields(request.form, ['title'])

        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            db.execute_query(
                stmt='UPDATE project SET title=?, last_updated=? WHERE id=?',
                args=(fields[0], date.today().strftime('%Y-%m-%d'), pk)
            )

            return make_response(jsonify({'message': 'Project updated successfully', 'project': {
                'id': pk,
                'user_id': project['user_id'],
                'title': fields[0],
                'creation_date': project['creation_date'],
                'last_update': date.today().strftime('%Y-%m-%d')
            }}), 200)

        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error updating project'}), 500)
    else:
        # Deletes a project
        db.execute_query('DELETE FROM project WHERE id=?', (pk,))
        return make_response(jsonify({'message': 'Project deleted successfully'}), 200)


@app.route('/api/projects/<int:pk>/collaborators/', methods=['GET', 'POST', 'DELETE'])
def collaborator_list(pk):
    """
    Collaborator list.
    Requires authorization

    """

    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    if not ((request.method == 'GET' and is_project_collaborator(db, pk, user['id'])) or
            is_user_project(db, pk, user['id'])):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user or the user is not a '
                                'collaborator'}),
            403)

    if request.method == 'GET':
        # Returns the list of collaborators of a project
        collaborators = db.execute_query(
            stmt='SELECT * FROM collaborator WHERE project_id=?',
            args=(pk,)
        ).fetchall()
        return make_response(jsonify({"collaborators": collaborators}))

    if request.method == 'POST':
        # Adds a collaborator to the project
        fields = get_required_fields(request.form, ['user_id'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            collaborator_id = int(fields[0])
            db.execute_update(
                stmt='INSERT INTO collaborator VALUES(null, ?, ?)',
                args=(pk, collaborator_id)
            )

            return make_response(jsonify({'message': 'Collaborator added successfully', 'collaborator': {
                'project_id': pk,
                'user_id': collaborator_id
            }}), 201)

        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error adding collaborator'}), 500)

    else:
        # Deletes a collaborator from the project
        fields = get_required_fields(request.form, ['user_id'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            # Checks if the user_id is a collaborator
            if not is_project_collaborator(db, pk, fields[0]):
                return make_response(jsonify({'message': 'Error: User is not a collaborator'}), 404)

            db.execute_query('DELETE FROM collaborator WHERE project_id=? AND user_id=?', (pk, fields[0]))

            return make_response(jsonify({'message': 'Collaborator removed successfully'}), 200)
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error deleting collaborator'}), 500)


@app.route('/api/projects/<int:pk>/tasks/', methods=['GET', 'POST'])
def task_list(pk):
    """
    Task list.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    if not ((request.method == 'GET' and is_project_collaborator(db, pk, user['id']))
            or is_user_project(db, pk, user['id'])):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user or the user is not a '
                                'collaborator'}),
            403)

    # Returns the list of tasks of a project
    if request.method == 'GET':
        tasks = db.execute_query('SELECT * FROM task WHERE project_id=?', (pk,)).fetchall()
        return make_response(jsonify({"tasks": tasks}))

    # Adds a task to project
    else:
        fields = get_required_fields(request.form, ['title'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        creation_date = date.today().strftime('%Y-%m-%d')

        try:
            task_id = db.execute_update(
                stmt='INSERT INTO task VALUES (null, ?, ?, ?, ?, ?)',
                args=(pk, pk, fields[0], creation_date, 0))

            return make_response(jsonify({'message': 'Task added successfully', 'task': {
                'id': task_id,
                'project_id': pk,
                'manager': pk,
                'title': fields[0],
                'creation_date': creation_date,
                'completed': 0
            }}), 201)
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error adding task'}), 500)


@app.route('/api/projects/<int:pk>/tasks/<int:task_pk>/', methods=['GET', 'PUT', 'DELETE'])
def task_detail(pk, task_pk):
    """
    Task detail.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 401)

    if not ((request.method == 'GET' or request.method == 'PUT' and is_project_collaborator(db, pk, user['id'])) or
            is_user_project(db, pk, user['id'])):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user or the user is not a '
                                'collaborator'}),
            403)

    task = db.execute_query(
        stmt='SELECT * FROM task WHERE project_id=? and id=?',
        args=(pk, task_pk)
    ).fetchone()

    # Returns a task
    if request.method == 'GET':
        return make_response(jsonify({'task': task}))
    # Updates a task
    elif request.method == 'PUT':
        fields = get_required_fields(request.form, ['title', 'completed'])

        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            if not is_task_manager(db, task_pk, user['id']):
                return make_response(jsonify({'message': 'Cant update the task: '
                                                         'The user is not the task manager'}),
                                     403)

            db.execute_query(
                stmt='UPDATE task SET title=?, completed=? WHERE id=?',
                args=(fields[0], fields[1], task_pk)
            )

            return make_response(jsonify({'message': 'Task updated successfully', 'task': {
                'id': task_pk,
                'project_id': pk,
                'title': fields[0],
                'creation_date': task['creation_date'],
                'completed': fields[1]
            }}), 200)
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            return make_response(jsonify({'message': 'Error updating task'}), 500)
    else:
        if not is_task_manager(db, task_pk, user['id']):
            return make_response(jsonify({'message': 'Cant update the task: '
                                                     'The user is not the task manager'}),
                                 403)

        # Deletes a task
        db.execute_query('DELETE FROM task WHERE id=?', (task_pk,))
        return make_response(jsonify({'message': 'Task deleted successfully'}), 200)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
