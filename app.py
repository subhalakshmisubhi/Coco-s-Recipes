from flask import Flask, render_template, request, redirect, url_for, session
from flask_mail import Mail, Message
import sqlite3

app = Flask(__name__)
app.secret_key = 'coco_super_secret_key'

# --- EMAIL CONFIGURATION (Using Gmail SMTP Example) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'         # Replace with your Gmail
app.config['MAIL_PASSWORD'] = 'your_gmail_app_password'     # Replace with your Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'

mail = Mail(app)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. Users Table (with role for admin vs user separation)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')

    # 2. Recipes Table (with nutritional breakdown)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            time TEXT,
            calories TEXT,
            protein TEXT,
            carbs TEXT,
            fats TEXT,
            steps TEXT,
            cuisine TEXT
        )
    ''')

    # 3. Ingredients Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ingredients (
            ingredient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            ingredient_name TEXT NOT NULL,
            quantity TEXT,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id) ON DELETE CASCADE
        )
    ''')

    # 4. Reviews & Comments Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipes (recipe_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # 5. Courses Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructor TEXT,
            date TEXT,
            description TEXT
        )
    ''')

    # 6. Course Registrations Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS course_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses (course_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
            UNIQUE(course_id, user_id)
        )
    ''')

    # Seed Admin User if not exists
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        conn.execute(
            'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
            ('admin', 'admin123', 'admin@coco.com', 'admin')
        )

    # Seed Sample Courses if not exists
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

# --- AUTHENTICATION ---
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
            session['role'] = user['role']
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                         (username, password, email, 'user'))
            conn.commit()
            conn.close()
            
            # --- SEND WELCOME EMAIL ---
            if email:
                try:
                    msg = Message(
                        subject='Welcome to Coco\'s Recipes!',
                        recipients=[email],
                        body=f'Hi {username},\n\nThank you for registering on Coco\'s Recipes! We are thrilled to have you join our culinary community.\n\nHappy cooking!\n- The Coco\'s Recipes Team'
                    )
                    mail.send(msg)
                except Exception as e:
                    print(f"Email could not be sent: {e}")
            
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Username already exists!')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- USER VIEWS ---
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    conn = get_db_connection()
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
    conn.close()
    return render_template('index.html', recipes=recipes)

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE recipe_id = ?', (recipe_id,)).fetchone()
    ingredients = conn.execute('SELECT * FROM ingredients WHERE recipe_id = ?', (recipe_id,)).fetchall()
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')
        if rating and comment:
            conn.execute('INSERT INTO reviews (recipe_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
                         (recipe_id, session['user_id'], rating, comment))
            conn.commit()
            return redirect(url_for('recipe_detail', recipe_id=recipe_id))
            
    reviews = conn.execute('''
        SELECT reviews.*, users.username FROM reviews 
        JOIN users ON reviews.user_id = users.user_id 
        WHERE reviews.recipe_id = ? ORDER BY review_id DESC
    ''', (recipe_id,)).fetchall()
    conn.close()
    
    return render_template('recipe_detail.html', recipe=recipe, ingredients=ingredients, reviews=reviews)

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    all_courses = conn.execute('SELECT * FROM courses').fetchall()
    user_regs = conn.execute('SELECT course_id FROM course_registrations WHERE user_id = ?', (session['user_id'],)).fetchall()
    registered_ids = [reg['course_id'] for reg in user_regs]
    conn.close()
    return render_template('workshops.html', courses=all_courses, registered_ids=registered_ids)

@app.route('/course/register/<int:course_id>', methods=['POST'])
def register_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO course_registrations (course_id, user_id) VALUES (?, ?)', (course_id, session['user_id']))
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        pass
    return redirect(url_for('courses'))

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        time = request.form.get('time')
        calories = request.form.get('calories')
        protein = request.form.get('protein')
        carbs = request.form.get('carbs')
        fats = request.form.get('fats')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        raw_ingredients = request.form.get('ingredients')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO recipes (title, time, calories, protein, carbs, fats, steps, cuisine) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (title, time, calories, protein, carbs, fats, steps, cuisine)
        )
        recipe_id = cursor.lastrowid
        
        if raw_ingredients:
            for item in raw_ingredients.split(','):
                if item.strip():
                    conn.execute('INSERT INTO ingredients (recipe_id, ingredient_name, quantity) VALUES (?, ?, ?)',
                                 (recipe_id, item.strip(), 'As needed'))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add_recipe.html')

@app.route('/recipe/edit/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE recipe_id = ?', (recipe_id,)).fetchone()
    
    if request.method == 'POST':
        title = request.form.get('title')
        time = request.form.get('time')
        calories = request.form.get('calories')
        protein = request.form.get('protein')
        carbs = request.form.get('carbs')
        fats = request.form.get('fats')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        
        conn.execute('''
            UPDATE recipes SET title = ?, time = ?, calories = ?, protein = ?, carbs = ?, fats = ?, steps = ?, cuisine = ?
            WHERE recipe_id = ?
        ''', (title, time, calories, protein, carbs, fats, steps, cuisine, recipe_id))
        conn.commit()
        conn.close()
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
        
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/recipe/delete/<int:recipe_id>', methods=['POST'])
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM recipes WHERE recipe_id = ?', (recipe_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# --- ADMIN VIEWS ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users, recipes=recipes, courses=courses)

@app.route('/admin/delete_recipe/<int:recipe_id>', methods=['POST'])
def admin_delete_recipe(recipe_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM recipes WHERE recipe_id = ?', (recipe_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
