"""
 Flask REST application

"""
import sqlite3

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
    fields = get_required_fields(['name', 'email', 'username', 'password'])
    if fields is None:
        return make_response(jsonify({'error': 'Missing required fields'}), 400)

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
    except Exception:
        return make_response(jsonify({'message': 'Error: Failed to register user'}), 500)


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.

    """
    user = get_valid_user(request.authorization)
    if user is None:
        return make_response(jsonify({"message": "Error: Invalid credentials"}), 403)

    # Returns user data
    if request.method == 'GET':
        return make_response(jsonify(user), 200)
    # Updates user data
    else:
        fields = get_required_fields(['name', 'email', 'username', 'password'])
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
        except Exception:
            return make_response(jsonify({'message': 'Error: Failed to update user'}), 500)


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
        project = db.execute_query('SELECT * FROM project WHERE id=?', (pk,)).fetchone()
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


# ===========
#  Auxiliary functions
# ===========

def get_valid_user(auth):
    """
    Checks if the given credentials are valid and returns its user
    :param auth: Request authorization header
    :return: User if the credentials are valid, null otherwise
    """
    if not request.authorization:
        return None

    user = db.execute_query(f'SELECT * FROM user WHERE username=? AND password=?', (
        auth.username,
        auth.password,
    )).fetchone()

    if not user:
        return None

    return user


def get_required_fields(required_fields):
    """
    Returns the required fields from the request
    :param required_fields: List of required fields
    :return: List of required fields if all are present, error message otherwise
    """
    missing_fields = [field for field in required_fields if not request.form.get(field)]
    if missing_fields:
        return None

    values = [request.form.get(field) for field in required_fields]
    return values


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
