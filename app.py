from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for
import mysql.connector
from mysql.connector import Error
import dicttoxml
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key-for-development')

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'user',       # change to your real MySQL password
    'database': 'pokemon_db', # must contain table `pokemon`
    'port': 3306
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def format_response(data, status_code=200):
    accept_header = request.headers.get('Accept', 'application/json')
    if 'application/xml' in accept_header:
        xml_data = dicttoxml.dicttoxml(data, custom_root='response', attr_type=False)
        response = make_response(xml_data, status_code)
        response.headers['Content-Type'] = 'application/xml'
        return response
    else:
        return jsonify(data), status_code

# ---------------- JWT auth ----------------

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return format_response({'error': 'Token is missing!'}, 401)

        try:
            if token.startswith('Bearer '):
                token = token[7:]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except jwt.ExpiredSignatureError:
            return format_response({'error': 'Token has expired!'}, 401)
        except jwt.InvalidTokenError:
            return format_response({'error': 'Token is invalid!'}, 401)

        return f(current_user, *args, **kwargs)

    return decorated

# ---------------- AUTH API ----------------

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'password')):
        return format_response({'error': 'Missing username or password'}, 400)

    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (data['username'], data['password']))
        connection.commit()
        cursor.close()
        connection.close()

        return format_response({
            'message': 'User registered successfully',
            'username': data['username']
        }, 201)
    except mysql.connector.IntegrityError:
        return format_response({'error': 'Username already exists'}, 400)
    except Error as e:
        return format_response({'error': str(e)}, 400)

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'password')):
        return format_response({'error': 'Missing username or password'}, 400)

    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (data['username'], data['password']))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if not user:
            return format_response({'error': 'Invalid username or password'}, 401)

        token = jwt.encode({
            'username': user['username'],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        return format_response({
            'message': 'Login successful',
            'token': token,
            'username': user['username']
        })
    except Error as e:
        return format_response({'error': str(e)}, 500)

# ---------------- WEB PAGES ----------------

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/web/pokemon')
def web_pokemon():
    connection = get_db_connection()
    if not connection:
        return "Database connection failed", 500

    search_name = request.args.get('search_name', '').strip()

    try:
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM pokemon WHERE 1=1"
        params = []

        if search_name:
            query += " AND name LIKE %s"
            params.append(f"%{search_name}%")

        query += " ORDER BY id"

        cursor.execute(query, params)
        pokemons = cursor.fetchall()
        cursor.close()
        connection.close()

        return render_template(
            'pokemon.html',
            pokemons=pokemons,
            search_name=search_name
        )
    except Error as e:
        return f"Error: {str(e)}", 500

# ---- NEW: web create Pokémon (for the Create button) ----

@app.route('/web/pokemon/create', methods=['GET', 'POST'])
def web_create_pokemon():
    if request.method == 'POST':
        name = request.form.get('name')
        base_experience = request.form.get('base_experience')
        height = request.form.get('height')
        weight = request.form.get('weight')

        connection = get_db_connection()
        if not connection:
            return "Database connection failed", 500

        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO pokemon (name, base_experience, height, weight)
                VALUES (%s, %s, %s, %s)
                """,
                (name, base_experience, height, weight)
            )
            connection.commit()
            cursor.close()
            connection.close()
            return redirect(url_for('web_pokemon'))
        except Error as e:
            return f"Error: {str(e)}", 400

    # GET: show the form
    return render_template('create_pokemon.html')

# ---------------- REST API INFO ----------------

@app.route('/api')
def api_home():
    return format_response({
        'message': 'Pokémon REST API with JWT Authentication',
        'version': '1.0',
        'authentication': {
            'POST /api/register': 'Register new user',
            'POST /api/login': 'Login and get JWT token'
        },
        'endpoints': {
            'GET /api/pokemon': 'Get all Pokémon (supports search with ?name=)',
            'GET /api/pokemon/<id>': 'Get Pokémon by ID',
            'POST /api/pokemon': 'Create new Pokémon (JWT required)',
            'PUT /api/pokemon/<id>': 'Update Pokémon (JWT required)',
            'DELETE /api/pokemon/<id>': 'Delete Pokémon (JWT required)'
        }
    })

# ---------------- POKÉMON API ----------------

@app.route('/api/pokemon/search', methods=['GET'])
def search_pokemon():
    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    search_name = request.args.get('name', '').strip()

    try:
        cursor = connection.cursor(dictionary=True)

        query = "SELECT * FROM pokemon WHERE 1=1"
        params = []

        if search_name:
            query += " AND name LIKE %s"
            params.append(f"%{search_name}%")

        query += " ORDER BY id"

        cursor.execute(query, params)
        pokemons = cursor.fetchall()
        cursor.close()
        connection.close()

        return format_response({
            'pokemons': pokemons,
            'count': len(pokemons),
            'search_criteria': {
                'name': search_name if search_name else None
            }
        })
    except Error as e:
        return format_response({'error': str(e)}, 500)

@app.route('/api/pokemon', methods=['GET'])
def get_all_pokemon():
    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pokemon ORDER BY id")
        pokemons = cursor.fetchall()
        cursor.close()
        connection.close()

        return format_response({'pokemons': pokemons, 'count': len(pokemons)})
    except Error as e:
        return format_response({'error': str(e)}, 500)

@app.route('/api/pokemon/<int:pokemon_id>', methods=['GET'])
def get_pokemon(pokemon_id):
    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM pokemon WHERE id = %s", (pokemon_id,))
        pokemon = cursor.fetchone()
        cursor.close()
        connection.close()

        if pokemon:
            return format_response({'pokemon': pokemon})
        else:
            return format_response({'error': 'Pokémon not found'}, 404)
    except Error as e:
        return format_response({'error': str(e)}, 500)

@app.route('/api/pokemon', methods=['POST'])
@token_required
def create_pokemon(current_user):
    data = request.get_json()

    if not data or not all(k in data for k in ('name', 'base_experience', 'height', 'weight')):
        return format_response(
            {'error': 'Missing required fields: name, base_experience, height, weight'},
            400
        )

    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO pokemon (name, base_experience, height, weight)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (data['name'], data['base_experience'], data['height'], data['weight'])
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        connection.close()

        pokemon_created = {
            'id': new_id,
            'name': data['name'],
            'base_experience': data['base_experience'],
            'height': data['height'],
            'weight': data['weight']
        }

        return format_response({
            'message': 'Pokémon created successfully',
            'pokemon': pokemon_created,
            'created_by': current_user
        }, 201)
    except Error as e:
        return format_response({'error': str(e)}, 400)

@app.route('/api/pokemon/<int:pokemon_id>', methods=['PUT'])
@token_required
def update_pokemon(current_user, pokemon_id):
    data = request.get_json()

    if not data:
        return format_response({'error': 'No data provided'}, 400)

    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor()

        update_fields = []
        values = []

        if 'name' in data:
            update_fields.append("name = %s")
            values.append(data['name'])
        if 'base_experience' in data:
            update_fields.append("base_experience = %s")
            values.append(data['base_experience'])
        if 'height' in data:
            update_fields.append("height = %s")
            values.append(data['height'])
        if 'weight' in data:
            update_fields.append("weight = %s")
            values.append(data['weight'])

        if not update_fields:
            return format_response({'error': 'No valid fields to update'}, 400)

        values.append(pokemon_id)
        query = f"UPDATE pokemon SET {', '.join(update_fields)} WHERE id = %s"

        cursor.execute(query, values)
        connection.commit()

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return format_response({'error': 'Pokémon not found'}, 404)

        cursor.close()
        connection.close()

        return format_response({
            'message': 'Pokémon updated successfully',
            'pokemon_id': pokemon_id,
            'updated_by': current_user
        })
    except Error as e:
        return format_response({'error': str(e)}, 400)

@app.route('/api/pokemon/<int:pokemon_id>', methods=['DELETE'])
@token_required
def delete_pokemon(current_user, pokemon_id):
    connection = get_db_connection()
    if not connection:
        return format_response({'error': 'Database connection failed'}, 500)

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM pokemon WHERE id = %s", (pokemon_id,))
        connection.commit()

        if cursor.rowcount == 0:
            cursor.close()
            connection.close()
            return format_response({'error': 'Pokémon not found'}, 404)

        cursor.close()
        connection.close()

        return format_response({
            'message': 'Pokémon deleted successfully',
            'pokemon_id': pokemon_id,
            'deleted_by': current_user
        })
    except Error as e:
        return format_response({'error': str(e)}, 500)

# ---------------- Error handlers ----------------

@app.errorhandler(404)
def not_found(error):
    return format_response({'error': 'Endpoint not found'}, 404)

@app.errorhandler(500)
def internal_error(error):
    return format_response({'error': 'Internal server error'}, 500)

if __name__ == '__main__':
    app.run(debug=True, port=5000)