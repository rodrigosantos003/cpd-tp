"""
Flask REST application
"""

import sqlite3
from datetime import date
from flask import Flask, request, jsonify, make_response
from flask_bcrypt import Bcrypt
from models import Database
import utils

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
    response = {'message': ''}
    status_code = 201

    # Get data
    fields = utils.get_required_fields(request.form, ['name', 'email', 'username', 'password'])
    if fields is None:
        response['message'] = 'Error: Missing required fields'
        status_code = 400
    else:
        # Create user in the database and send response
        try:
            hashed_password = bcrypt.generate_password_hash(fields[3]).decode('utf-8')

            user_id = db.execute_update(
                stmt='INSERT INTO user (name, email, username, password) VALUES (?, ?, ?, ?)',
                args=(fields[0], fields[1], fields[2], hashed_password)
            )

            response['message'] = 'User registered successfully'
            response['user'] = {
                'id': user_id,
                'name': fields[0],
                'email': fields[1],
                'username': fields[2],
                'password': hashed_password
            }
        except (sqlite3.Error, Exception) as e:
            app.logger.error('%s', str(e))
            response['message'] = 'Error: Failed to register user'
            status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    else:
        if request.method == 'GET':
            response = {'user': user}
        elif request.method == 'PUT':
            fields = utils.get_required_fields(request.form, ['name', 'email',
                                                              'username', 'password'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    hashed_password = bcrypt.generate_password_hash(fields[3]).decode('utf-8')

                    db.execute_query(
                        stmt='UPDATE user SET name=?, email=?, username=?, password=? WHERE id=?',
                        args=(fields[0], fields[1], fields[2], hashed_password, user['id'])
                    )

                    response['message'] = 'User updated successfully'
                    response['user'] = {
                        'id': user['id'],
                        'name': fields[0],
                        'email': fields[1],
                        'username': fields[2],
                        'password': hashed_password
                    }
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error: Failed to update user'
                    status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/projects/', methods=['GET', 'POST'])
def project_list():
    """
    Project list.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    else:
        if request.method == 'GET':
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

            response = {'projects': projects}
        elif request.method == 'POST':
            fields = utils.get_required_fields(request.form, ['title'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    current_date = date.today().strftime('%Y-%m-%d')
                    project_id = db.execute_update(
                        stmt='INSERT INTO project VALUES (null, ?, ?, ?, ?)',
                        args=(user['id'], fields[0], current_date, current_date)
                    )

                    response['message'] = 'Project added successfully'
                    response['project'] = {
                        'id': project_id,
                        'user_id': user['id'],
                        'title': fields[0],
                        'creation_date': current_date,
                        'last_update': current_date
                    }

                    status_code = 201
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error adding project'
                    status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/projects/<int:pk>/', methods=['GET', 'PUT', 'DELETE'])
def project_detail(pk):
    """
    Project detail.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    elif not ((request.method == 'GET' and utils.is_project_collaborator(db, pk, user['id'])) or
              utils.is_user_project(db, pk, user['id'])):
        response['message'] = ('The requested project doesnt belong '
                               'to the logged user or the user is not a collaborator')
        status_code = 403
    else:
        if request.method == 'GET':
            project = db.execute_query(
                stmt='SELECT * FROM project WHERE id=?',
                args=(pk,)
            ).fetchone()
            response = {'project': project}
        elif request.method == 'PUT':
            project = db.execute_query(
                stmt='SELECT * FROM project WHERE id=?',
                args=(pk,)
            ).fetchone()

            fields = utils.get_required_fields(request.form, ['title'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    db.execute_query(
                        stmt='UPDATE project SET title=?, last_updated=? WHERE id=?',
                        args=(fields[0], date.today().strftime('%Y-%m-%d'), pk)
                    )

                    response['message'] = 'Project updated successfully'
                    response['project'] = {
                        'id': pk,
                        'user_id': project['user_id'],
                        'title': fields[0],
                        'creation_date': project['creation_date'],
                        'last_update': date.today().strftime('%Y-%m-%d')
                    }
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error updating project'
                    status_code = 500
        elif request.method == 'DELETE':
            try:
                db.execute_query('DELETE FROM project WHERE id=?', (pk,))
                response['message'] = 'Project deleted successfully'
            except (sqlite3.Error, Exception) as e:
                app.logger.error('%s', str(e))
                response['message'] = 'Error deleting project'
                status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/projects/<int:pk>/collaborators/', methods=['GET', 'POST', 'DELETE'])
def collaborator_list(pk):
    """
    Collaborator list.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    elif not ((request.method == 'GET' and utils.is_project_collaborator(db, pk, user['id'])) or
              utils.is_user_project(db, pk, user['id'])):
        response['message'] = ('The requested project doesnt belong '
                               'to the logged user or the user is not a collaborator')
        status_code = 403
    else:
        if request.method == 'GET':
            collaborators = db.execute_query(
                stmt='SELECT * FROM collaborator WHERE project_id=?',
                args=(pk,)
            ).fetchall()
            response = {'collaborators': collaborators}
        elif request.method == 'POST':
            fields = utils.get_required_fields(request.form, ['user_id'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    collaborator_id = int(fields[0])
                    db.execute_update(
                        stmt='INSERT INTO collaborator VALUES(null, ?, ?)',
                        args=(pk, collaborator_id)
                    )
                    response['message'] = 'Collaborator added successfully'
                    response['collaborator'] = {
                        'project_id': pk,
                        'user_id': collaborator_id
                    }
                    status_code = 201
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error adding collaborator'
                    status_code = 500
        elif request.method == 'DELETE':
            fields = utils.get_required_fields(request.form, ['user_id'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    if not utils.is_project_collaborator(db, pk, fields[0]):
                        response['message'] = 'Error: User is not a collaborator'
                        status_code = 404
                    else:
                        db.execute_query(
                            stmt='DELETE FROM collaborator WHERE project_id=? AND user_id=?',
                            args=(pk, fields[0])
                        )
                        response['message'] = 'Collaborator removed successfully'
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error deleting collaborator'
                    status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/projects/<int:pk>/tasks/', methods=['GET', 'POST'])
def task_list(pk):
    """
    Task list.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    elif not ((request.method == 'GET' and utils.is_project_collaborator(db, pk, user['id']))
              or utils.is_user_project(db, pk, user['id'])):
        response['message'] = ('The requested project doesnt belong '
                               'to the logged user or the user is not a collaborator')
        status_code = 403
    else:
        if request.method == 'GET':
            tasks = db.execute_query('SELECT * FROM task WHERE project_id=?', (pk,)).fetchall()
            response = {'tasks': tasks}
        elif request.method == 'POST':
            fields = utils.get_required_fields(request.form, ['title'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                creation_date = date.today().strftime('%Y-%m-%d')
                try:
                    task_id = db.execute_update(
                        stmt='INSERT INTO task VALUES (null, ?, ?, ?, ?, ?)',
                        args=(pk, pk, fields[0], creation_date, 0)
                    )
                    response['message'] = 'Task added successfully'
                    response['task'] = {
                        'id': task_id,
                        'project_id': pk,
                        'manager': pk,
                        'title': fields[0],
                        'creation_date': creation_date,
                        'completed': 0
                    }
                    status_code = 201
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error adding task'
                    status_code = 500

    return make_response(jsonify(response), status_code)


@app.route('/api/projects/<int:pk>/tasks/<int:task_pk>/', methods=['GET', 'PUT', 'DELETE'])
def task_detail(pk, task_pk):
    """
    Task detail.
    Requires authorization.
    """
    response = {'message': ''}
    status_code = 200

    user = utils.get_valid_user(db, request.authorization, bcrypt)
    if user is None:
        response['message'] = 'Error: Invalid credentials'
        status_code = 401
    elif not ((request.method == 'GET' or request.method == 'PUT'
               and utils.is_project_collaborator(db, pk, user['id'])) or
              utils.is_project_collaborator(db, pk, user['id'])):
        response['message'] = ('The requested project doesnt belong '
                               'to the logged user or the user is not a collaborator')
        status_code = 403
    else:
        task = db.execute_query(
            stmt='SELECT * FROM task WHERE project_id=? and id=?',
            args=(pk, task_pk)
        ).fetchone()

        if request.method == 'GET':
            response = {'task': task}
        elif request.method == 'PUT':
            fields = utils.get_required_fields(request.form, ['title', 'completed'])
            if fields is None:
                response['message'] = 'Error: Missing required fields'
                status_code = 400
            else:
                try:
                    if not utils.is_task_manager(db, task_pk, user['id']):
                        response['message'] = ('Cant update the task: '
                                               'The user is not the task manager')
                        status_code = 403
                    else:
                        db.execute_query(
                            stmt='UPDATE task SET title=?, completed=? WHERE id=?',
                            args=(fields[0], fields[1], task_pk)
                        )
                        response['message'] = 'Task updated successfully'
                        response['task'] = {
                            'id': task_pk,
                            'project_id': pk,
                            'title': fields[0],
                            'creation_date': task['creation_date'],
                            'completed': fields[1]
                        }
                except (sqlite3.Error, Exception) as e:
                    app.logger.error('%s', str(e))
                    response['message'] = 'Error updating task'
                    status_code = 500
        elif request.method == 'DELETE':
            try:
                if not utils.is_task_manager(db, task_pk, user['id']):
                    response['message'] = 'Cant update the task: The user is not the task manager'
                    status_code = 403
                else:
                    db.execute_query('DELETE FROM task WHERE id=?', (task_pk,))
                    response['message'] = 'Task deleted successfully'
            except (sqlite3.Error, Exception) as e:
                app.logger.error('%s', str(e))
                response['message'] = 'Error deleting task'
                status_code = 500

    return make_response(jsonify(response), status_code)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
