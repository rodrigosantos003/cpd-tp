"""
 Flask REST application

"""

from flask import Flask, request, jsonify, make_response
from models import Database


# ==========
#  Settings
# ==========

app = Flask(__name__)
app.config['STATIC_URL_PATH'] = '/static'
app.config['DEBUG'] = True


# ==========
#  Database
# ==========

# Creates an sqlite database in memory
db = Database(filename=':memory:', schema='schema.sql')
db.recreate()


# ===========
#  Web views
# ===========

@app.route('/')
def index():
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
    pass


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.

    """
    user = db.execute_query(f'SELECT * FROM user WHERE username=? AND password=?', (
        request.authorization.username,
        request.authorization.password,
    )).fetchone()

    if request.method == 'GET':
        # Returns user data
        return make_response(jsonify(user))
    else:
        # Updates user data
        pass


@app.route('/api/projects/', methods=['GET', 'POST'])
def project_list():
    """
    Project list.
    Requires authorization.

    """
    if request.method == 'GET':
        # Returns the list of projects of a user
        projects = db.execute_query('SELECT * FROM project').fetchall()
        return make_response(jsonify(projects))
    else:
        # Adds a project to the list
        pass


@app.route('/api/projects/<int:pk>/', methods=['GET', 'PUT', 'DELETE'])
def project_detail(pk):
    """
    Project detail.
    Requires authorization.

    """
    if request.method == 'GET':
        # Returns a project
        project = db.execute_query('SELECT * FROM project WHERE id=?', (pk, )).fetchone()
        return make_response(jsonify(project))
    elif request.method == 'PUT':
        # Updates a project
        pass
    else:
        # Deletes a project
        pass


@app.route('/api/projects/<int:pk>/tasks/', methods=['GET', 'POST'])
def task_list(pk):
    """
    Task list.
    Requires authorization.

    """
    if request.method == 'GET':
        # Returns the list of tasks of a project
        tasks = db.execute_query('SELECT * FROM task WHERE project_id=?', (pk,)).fetchall()
        return make_response(jsonify(tasks))
    else:
        # Adds a task to project
        pass


@app.route('/api/projects/<int:pk>/tasks/<int:task_pk>/', methods=['GET', 'PUT', 'DELETE'])
def task_detail(pk, task_pk):
    """
    Task detail.
    Requires authorization.

    """
    if request.method == 'GET':
        # Returns a task
        task = db.execute_query('SELECT * FROM task WHERE project_id=? and id=?', (pk, task_pk)).fetchone()
        return make_response(jsonify(task))
    elif request.method == 'PUT':
        # Updates a task
        pass
    else:
        # Deletes a task
        pass


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
