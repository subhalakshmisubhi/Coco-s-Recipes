from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

template_dir = os.path.abspath(os.path.dirname(__file__)) + '/templates'
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'coco_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. Users Table (with user_id)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        )
    ''')

    # 2. Recipes Table (with recipe_id)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            time TEXT,
            calories TEXT,
            steps TEXT,
            cuisine TEXT
        )
    ''')

    # 3. Ingredients Table (with ingredient_id)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_name TEXT NOT NULL,
            quantity TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id)
        )
    ''')

    # 4. Courses Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructor TEXT,
            date TEXT,
            description TEXT
        )
    ''')

    # 5. Course Registrations Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses (course_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Seed Admin User
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        conn.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            ('admin', 'coco123', 'admin@coco.com')
        )

    # Seed Sample Workshops
    cursor.execute('SELECT COUNT(*) FROM courses')
    if cursor.fetchone()[0] == 0:
        sample_courses = [
            ('Mastering Italian Pasta', 'Chef Luigi', 'October 15, 2026', 'Learn handmade pasta from scratch.'),
            ('Artisan Baking & Pastries', 'Chef Coco', 'October 22, 2026', 'Discover professional baking techniques.')
        ]
        conn.executemany(
            'INSERT INTO courses (title, instructor, date, description) VALUES (?, ?, ?, ?)',
            sample_courses
        )

    conn.commit()
    conn.close()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password or not email:
            return render_template('register.html', error='All fields are required!')
            
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists!')
            
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
    
    recipes_with_ingredients = []
    for recipe in recipes:
        recipe_dict = dict(recipe)
        ingredients = conn.execute('SELECT * FROM ingredients WHERE recipe_id = ?', (recipe['recipe_id'],)).fetchall()
        recipe_dict['ingredients_list'] = ingredients
        recipes_with_ingredients.append(recipe_dict)
        
    conn.close()
    return render_template('index.html', recipes=recipes_with_ingredients)

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('workshops.html', courses=all_courses)

@app.route('/course/register/<int:course_id>', methods=['POST'])
def register_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('INSERT INTO course_registrations (course_id, user_id) VALUES (?, ?)', (course_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('courses'))

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        time = request.form.get('time')
        calories = request.form.get('calories')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        raw_ingredients = request.form.get('ingredients')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO recipes (title, time, calories, steps, cuisine) VALUES (?, ?, ?, ?, ?)',
            (title, time, calories, steps, cuisine)
        )
        recipe_id = cursor.lastrowid
        
        if raw_ingredients:
            ingredient_items = [item.strip() for item in raw_ingredients.split(',')]
            for item in ingredient_items:
                if item:
                    conn.execute(
                        'INSERT INTO ingredients (recipe_id, ingredient_name, quantity) VALUES (?, ?, ?)',
                        (recipe_id, item, 'As needed')
                    )
                    
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add_recipe.html')

@app.route('/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE recipe_id = ?', (recipe_id,)).fetchone()
    
    if request.method == 'POST':
        title = request.form.get('title')
        time = request.form.get('time')
        calories = request.form.get('calories')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        
        conn.execute(
            'UPDATE recipes SET title = ?, time = ?, calories = ?, steps = ?, cuisine = ? WHERE recipe_id = ?',
            (title, time, calories, steps, cuisine, recipe_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM ingredients WHERE recipe_id = ?', (recipe_id,))
    conn.execute('DELETE FROM recipes WHERE recipe_id = ?', (recipe_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
