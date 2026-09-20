from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'coco_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Recipes table with cuisine support
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            time TEXT,
            calories TEXT,
            ingredients TEXT,
            steps TEXT,
            cuisine TEXT
        )
    ''')

    # Workshops table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS workshops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructor TEXT,
            date TEXT,
            description TEXT
        )
    ''')

    # Add sample workshop if table is empty
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM workshops')
    if cursor.fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO workshops (title, instructor, date, description) VALUES (?, ?, ?, ?)",
            ("Mastering Italian Pasta", "Chef Coco", "Oct 15, 2026", "Learn to make fresh pasta from scratch!")
        )
        conn.execute(
            "INSERT INTO workshops (title, instructor, date, description) VALUES (?, ?, ?, ?)",
            ("Baking Artisan Sourdough", "Chef Marco", "Oct 22, 2026", "Discover the secrets of maintaining a starter and baking crusty artisan bread.")
        )
        conn.commit()

    conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'coco123':
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user' not in session:
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

@app.route('/workshops')
def workshops():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    workshops = conn.execute('SELECT * FROM workshops').fetchall()
    conn.close()
    return render_template('workshops.html', workshops=workshops)

@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
    if 'user' not in session:
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

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        title = request.form.get('title')
        time = request.form.get('time')
        calories = request.form.get('calories')
        ingredients = request.form.get('ingredients')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')
        
        conn.execute(
            'UPDATE recipes SET title = ?, time = ?, calories = ?, ingredients = ?, steps = ?, cuisine = ? WHERE id = ?',
            (title, time, calories, ingredients, steps, cuisine, id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
        
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/delete/<int:id>')
def delete_recipe(id):
    if 'user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM recipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
