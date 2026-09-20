from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'coco_secret_key_123'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Recipes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            time TEXT,
            calories TEXT,
            ingredients TEXT,
            steps TEXT
        )
    ''')
    #Cuisine Text
    def init_db():
    conn = get_db_connection()
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
    @app.route('/')
    ...
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
    
    # Add a sample workshop if table is empty
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM workshops')
    if cursor.fetchone()[0] == 0:
        conn.execute("INSERT INTO workshops (title, instructor, date, description) VALUES (?, ?, ?, ?)",
                     ("Mastering Italian Pasta", "Chef Coco", "Oct 15, 2026", "Learn to make fresh handmade pasta from scratch with classic sauces!"))
        conn.execute("INSERT INTO workshops (title, instructor, date, description) VALUES (?, ?, ?, ?)",
                     ("Baking Artisan Sourdough", "Chef Marco", "Oct 22, 2026", "Discover the secrets of maintaining a starter and baking crusty artisan bread."))
        conn.commit()
        
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    if search_query:
        recipes = conn.execute(
            'SELECT * FROM recipes WHERE title LIKE ? OR ingredients LIKE ?',
            ('%' + search_query + '%', '%' + search_query + '%')
        ).fetchall()
    else:
        recipes = conn.execute('SELECT * FROM recipes').fetchall()
    conn.close()
    return render_template('index.html', recipes=recipes, search=search_query)

@app.route('/workshops')
def workshops():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    workshops_list = conn.execute('SELECT * FROM workshops').fetchall()
    conn.close()
    return render_template('workshops.html', workshops=workshops_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'coco123':
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

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
        ingredients = request.form.get('ingredients')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')   # <-- Add this line

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO recipes (title, time, calories, ingredients, steps, cuisine) VALUES (?, ?, ?, ?, ?, ?)', # <-- Add cuisine and one more ?
            (title, time, calories, ingredients, steps, cuisine) # <-- Add cuisine here
        )
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO recipes (title, time, calories, ingredients, steps) VALUES (?, ?, ?, ?, ?)',
            (title, time, calories, ingredients, steps)
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
        ingredients = request.form.get('ingredients')
        steps = request.form.get('steps')
        cuisine = request.form.get('cuisine')   # <-- Add this line

        conn.execute(
            'UPDATE recipes SET title = ?, time = ?, calories = ?, ingredients = ?, steps = ?, cuisine = ? WHERE id = ?', # <-- Add cuisine = ?
            (title, time, calories, ingredients, steps, cuisine, id) # <-- Add cuisine here
        )
        steps = request.form.get('steps')
        
        conn.execute(
            'UPDATE recipes SET title = ?, time = ?, calories = ?, ingredients = ?, steps = ? WHERE id = ?',
            (title, time, calories, ingredients, steps, id)
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
    app.run(debug=True, port=5000)
