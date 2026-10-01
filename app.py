import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'coco_super_secret_key'

# --- EMAIL CONFIGURATION (Using Gmail App Password) ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'subhalakshmisubhi@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'ejdn ianf omil iulm'  # Replace with your 16-character app password
app.config['MAIL_DEFAULT_SENDER'] = 'subhalakshmisubhi@gmail.com'

mail = Mail(app)


def get_db_connection():
  conn = sqlite3.connect('database.db', timeout=15)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  with get_db_connection() as conn:
    # Users Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
    # Recipes Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                instructions TEXT NOT NULL,
                category TEXT,
                calories INTEGER,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    # Courses / Workshops Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                mentor TEXT NOT NULL
            )
        ''')
    # Course Registrations Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS course_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                user_id INTEGER,
                UNIQUE(course_id, user_id),
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    conn.commit()

    # Create default admin user if not exists
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
      conn.execute(
          'INSERT INTO users (username, password, email, role) VALUES (?, ?,'
          ' ?, ?)',
          ('admin', 'admin123', 'admin@cocosrecipes.com', 'admin'),
      )
      conn.commit()


# Initialize Database on Startup
init_db()


@app.route('/')
def index():
  with get_db_connection() as conn:
    recipes = conn.execute('SELECT * FROM recipes LIMIT 6').fetchall()
  return render_template('index.html', recipes=recipes)


@app.route('/recipes')
def recipes():
  with get_db_connection() as conn:
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
  return render_template('recipes.html', recipes=recipes)


@app.route('/recipe/<int:id>')
def recipe_detail(id):
  with get_db_connection() as conn:
    recipe = conn.execute(
        'SELECT * FROM recipes WHERE id = ?', (id,)
    ).fetchone()
  return render_template('recipe_detail.html', recipe=recipe)


@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  if request.method == 'POST':
    title = request.form.get('title')
    ingredients = request.form.get('ingredients')
    instructions = request.form.get('instructions')
    category = request.form.get('category')
    calories = request.form.get('calories', 0)

    with get_db_connection() as conn:
      conn.execute(
          'INSERT INTO recipes (title, ingredients, instructions, category,'
          ' calories, user_id) VALUES (?, ?, ?, ?, ?, ?)',
          (
              title,
              ingredients,
              instructions,
              category,
              calories,
              session['user_id'],
          ),
      )
      conn.commit()
    return redirect(url_for('recipes'))

  return render_template('add_recipe.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    recipe = conn.execute(
        'SELECT * FROM recipes WHERE id = ?', (id,)
    ).fetchone()

  if not recipe:
    return 'Recipe not found', 404

  if request.method == 'POST':
    title = request.form.get('title')
    ingredients = request.form.get('ingredients')
    instructions = request.form.get('instructions')
    category = request.form.get('category')
    calories = request.form.get('calories', 0)

    with get_db_connection() as conn:
      conn.execute(
          'UPDATE recipes SET title = ?, ingredients = ?, instructions = ?,'
          ' category = ?, calories = ? WHERE id = ?',
          (title, ingredients, instructions, category, calories, id),
      )
      conn.commit()
    return redirect(url_for('recipe_detail', id=id))

  return render_template('edit_recipe.html', recipe=recipe)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_recipe(id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    conn.execute('DELETE FROM recipes WHERE id = ?', (id,))
    conn.commit()
  return redirect(url_for('recipes'))


@app.route('/courses')
def courses():
  with get_db_connection() as conn:
    courses = conn.execute('SELECT * FROM courses').fetchall()
    registered_ids = []
    if 'user_id' in session:
      regs = conn.execute(
          'SELECT course_id FROM course_registrations WHERE user_id = ?',
          (session['user_id'],),
      ).fetchall()
      registered_ids = [r['course_id'] for r in regs]
  return render_template(
      'courses.html', courses=courses, registered_ids=registered_ids
  )


@app.route('/course/register/<int:course_id>', methods=['POST'])
def register_course(course_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  try:
    with get_db_connection() as conn:
      conn.execute(
          'INSERT INTO course_registrations (course_id, user_id) VALUES (?, ?)',
          (course_id, session['user_id']),
      )
      conn.commit()
  except sqlite3.IntegrityError:
    pass  # Already registered, skip gracefully

  return redirect(url_for('courses'))


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')

    try:
      with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO users (username, password, email, role) VALUES (?, ?,'
            ' ?, ?)',
            (username, password, email, 'user'),
        )
        conn.commit()

      # Send welcome email
      if email:
        try:
          msg = Message(
              subject="Welcome to Coco's Recipes!",
              recipients=[email],
              body=(
                  f'Hi {username},\n\nThank you for registering on Coco\'s'
                  ' Recipes! We are thrilled to have you join our culinary'
                  ' community.\n\nHappy cooking!\n- The Coco\'s Recipes Team'
              ),
          )
          mail.send(msg)
        except Exception as e:
          print(f'Email dispatch failed: {e}')

      return redirect(url_for('login'))
    except sqlite3.IntegrityError:
      return render_template(
          'register.html', error='Username already exists!'
      )

  return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')

    with get_db_connection() as conn:
      user = conn.execute(
          'SELECT * FROM users WHERE username = ? AND password = ?',
          (username, password),
      ).fetchone()

    if user:
      session['user_id'] = user['id']
      session['username'] = user['username']
      session['role'] = user['role']
      return redirect(url_for('index'))
    else:
      return render_template('login.html', error='Invalid username or password')

  return render_template('login.html')


@app.route('/logout')
def logout():
  session.clear()
  return redirect(url_for('login'))


@app.route('/admin')
def admin():
  if session.get('role') != 'admin':
    return redirect(url_for('index'))

  with get_db_connection() as conn:
    users = conn.execute('SELECT * FROM users').fetchall()
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
  return render_template('admin.html', users=users, recipes=recipes)


if __name__ == '__main__':
  app.run(debug=True, port=5000)
