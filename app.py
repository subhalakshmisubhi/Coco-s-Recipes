from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

# Explicitly set the template folder path to avoid any TemplateNotFound errors
template_dir = os.path.abspath(os.path.dirname(__file__)) + '/templates'
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'coco_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. User / Member Table (with user_id)
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
            ingredients TEXT,
            steps TEXT,
            cuisine TEXT
        )
    ''')

    # 3. Ingredients Table (with ingredient_id and foreign key to recipe)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_name TEXT NOT NULL,
            quantity TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id)
        )
    ''')

    # 4. Courses / Workshops Table (with course_id)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructor TEXT,
            date TEXT,
            description TEXT
        )
    ''')

    # 5. Course Registrations Table (with registration tracking)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses (course_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # 6. Reviews Table (with review_id)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Insert a default admin user so you can log in immediately
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        conn.execute(
            'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
            ('admin', 'coco123', 'admin@coco.com')
        )

    # Insert sample courses/workshops if none exist
    cursor.execute('SELECT COUNT(*) FROM courses')
    if cursor.fetchone()[0] == 0:
        sample_courses = [
            ('Mastering Italian Pasta', 'Chef Luigi', 'October 15, 2026', 'Learn the secrets of making handmade pasta from scratch, classic carbonara, and rich marinara sauce.'),
            ('Artisan Baking & Pastries', 'Chef Coco', 'October 22, 2026', 'Discover professional baking techniques for croissants, French macarons, and artisan sourdough bread.'),
            ('Quick & Healthy Weeknight Meals', 'Chef Maya', 'November 5, 2026', 'Master fast, nutritious, and flavorful meals designed for busy schedules without compromising on taste.')
        ]
        conn.executemany(
            'INSERT INTO courses (title, instructor, date, description) VALUES (?, ?, ?, ?)',
            sample_courses
        )

    conn.commit()
    conn.close()

# --- Authentication Routes ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
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

# --- Main App Routes ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    conn = get_db_connection()
    if search:
        recipes = conn.execute(
            "SELECT * FROM recipes WHERE title LIKE ? OR ingredients LIKE ?",
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        recipes = conn.execute('SELECT * FROM recipes').fetchall()
    conn.close()
    
    return render_template('index.html', recipes=recipes, search=search)

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
    conn.execute(
        'INSERT INTO course_registrations (course_id, user_id) VALUES (?, ?)',
        (course_id, session['user_id'])
    )
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
        ingredients = request.form.get('ingredients')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO recipes (title, time, calories, ingredients, steps, cuisine) VALUES (?, ?, ?, ?, ?, ?)',
            (title, time, calories, ingredients, steps, cuisine)
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
        ingredients = request.form.get('ingredients')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        
        conn.execute(
            'UPDATE recipes SET title = ?, time = ?, calories = ?, ingredients = ?, steps = ?, cuisine = ? WHERE recipe_id = ?',
            (title, time, calories, ingredients, steps, cuisine, recipe_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
