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
    # Get required fields
    name = request.form.get('name', type=str)
    email = request.form.get('email', type=str)
    username = request.form.get('username', type=str)
    password = request.form.get('password', type=str)

    if not name or not email or not username or not password:
        return make_response(jsonify({'error': 'Missing required fields'}), 400)

    # Create user on database and send response
    try:
        db.execute_query(
            stmt='INSERT INTO user VALUES(null, ?, ?, ?, ?)',
            args=(name, email, username, password)
        )

        return make_response(jsonify({'success': 'User registered successfully'}), 200)
    except Exception:
        return make_response(jsonify({'error': 'Failed to register user'}), 500)


@app.route('/api/user/', methods=['GET', 'PUT'])
def user_detail():
    """
    Returns or updates current user.
    Requires authorization.

    """
    user = get_valid_user(request.authorization)
    if user is None:
        return make_response(jsonify({"error": "Invalid credentials"}), 403)

    # Returns user data
    if request.method == 'GET':
        return make_response(jsonify(user), 200)
    # Updates user data
    else:
        # Get required fields
        name = request.form.get('name', type=str)
        email = request.form.get('email', type=str)
        username = request.form.get('username', type=str)
        password = request.form.get('password', type=str)

        if not name or not email or not username or not password:
            return make_response(jsonify({'error': 'Missing required fields'}), 400)

        # Update user on database
        try:
            db.execute_query(
                stmt='UPDATE user SET name=?, email=?, username=?, password=? WHERE id=?',
                args=(name, email, username, password, user['id'])
            )

            return make_response(jsonify({'success': 'User updated successfully'}), 200)
        except Exception:
            return make_response(jsonify({'error': 'Failed to update user'}), 500)


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

    return user


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
