"""
 Flask REST application

"""
import sqlite3

from datetime import date
from flask import Flask, request, jsonify, make_response
from models import Database
from utils import get_valid_user, get_required_fields, is_user_project

# ==========
#  Settings
# ==========

app = Flask(__name__)
app.config['STATIC_URL_PATH'] = '/static'
app.config['DEBUG'] = True

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
        user_id = db.execute_update(
            stmt='INSERT INTO user VALUES(null, ?, ?, ?, ?)',
            args=(fields[0], fields[1], fields[2], fields[3])
        )

        return make_response(jsonify({'message': 'User registered successfully', 'user': {
            'id': user_id,
            'name': fields[0],
            'email': fields[1],
            'username': fields[2],
            'password': fields[3]
        }}), 201)
    except (sqlite3.Error, Exception):
        return make_response(jsonify({'message': 'Error: Failed to register user'}), 500)


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

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
        except (sqlite3.Error, Exception):
            return make_response(jsonify({'message': 'Error: Failed to update user'}), 500)


@app.route('/api/projects/', methods=['GET', 'POST'])
def project_list():
    """
    Project list.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

    if request.method == 'GET':
        # Returns the list of projects of a user
        projects = db.execute_query('SELECT * FROM project WHERE user_id=?', (user['id'],)).fetchall()
        return make_response(jsonify({"projects": projects}))
    else:
        # Adds a project to the list
        fields = get_required_fields(request.form, ['title'])
        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
            currentDate = date.today().strftime('%Y-%m-%d')
            project_id = db.execute_update(
                stmt='INSERT INTO project VALUES (null, ?, ?, ?, ?)',
                args=(user['id'], fields[0], currentDate, currentDate)
            )

            return make_response(jsonify({'message': 'Project added successfully', 'project': {
                'id': project_id,
                'user_id': user['id'],
                'title': fields[0],
                'creation_date': currentDate,
                'last_update': currentDate
            }}), 201)
        except (sqlite3.Error, Exception):
            return make_response(jsonify({'message': 'Error adding project'}), 500)
        pass


@app.route('/api/projects/<int:pk>/', methods=['GET', 'PUT', 'DELETE'])
def project_detail(pk):
    """
    Project detail.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

    if not is_user_project(db, pk, user['id']):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user'}),
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

        except (sqlite3.Error, Exception):
            return make_response(jsonify({'message': 'Error updating project'}), 500)
        pass
    else:
        # Deletes a project
        db.execute_query('DELETE FROM project WHERE id=?', (pk,))
        return make_response(jsonify({'message': 'Project deleted successfully'}), 200)
        pass


@app.route('/api/projects/<int:pk>/tasks/', methods=['GET', 'POST'])
def task_list(pk):
    """
    Task list.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

    if not is_user_project(db, pk, user['id']):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user'}),
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
                stmt='INSERT INTO task VALUES (null, ?, ?, ?, ?)',
                args=(pk, fields[0], creation_date, 0))

            return make_response(jsonify({'message': 'Task added successfully', 'task': {
                'id': task_id,
                'project_id': pk,
                'title': fields[0],
                'creation_date': creation_date,
                'completed': 0
            }}), 201)
        except (sqlite3.Error, Exception):
            return make_response(jsonify({'message': 'Error adding task'}), 500)


@app.route('/api/projects/<int:pk>/tasks/<int:task_pk>/', methods=['GET', 'PUT', 'DELETE'])
def task_detail(pk, task_pk):
    """
    Task detail.
    Requires authorization.

    """
    user = get_valid_user(db, request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

    if not is_user_project(db, pk, user['id']):
        return make_response(
            jsonify({'message': 'The requested project doesnt belong to the logged user'}),
            403)

    if request.method == 'GET':
        # Returns a task
        task = db.execute_query(
            stmt='SELECT * FROM task WHERE project_id=? and id=?',
            args=(pk, task_pk)
        ).fetchone()
        return make_response(jsonify({'task': task}))
    elif request.method == 'PUT':
        # Updates a task
        task = db.execute_query(
            stmt='SELECT * FROM task WHERE project_id=? and id=?',
            args=(pk, task_pk)
        ).fetchone()

        fields = get_required_fields(request.form, ['title', 'completed'])

        if fields is None:
            return make_response(jsonify({'message': 'Error: Missing required fields'}), 400)

        try:
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
        except (sqlite3.Error, Exception):
            return make_response(jsonify({'message': 'Error updating task'}), 500)
        pass
    else:
        # Deletes a task
        db.execute_query('DELETE FROM task WHERE id=?', (task_pk,))
        return make_response(jsonify({'message': 'Task deleted successfully'}), 200)
        pass


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
