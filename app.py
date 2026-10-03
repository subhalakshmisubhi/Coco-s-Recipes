import re
import sqlite3
from flask import Flask, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'coco_super_secret_key'

# --- EMAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = (
    'subhalakshmisubhi@gmail.com'  # Replace with your actual email
)
app.config['MAIL_PASSWORD'] = (
    'ejdn ianf omil iulm'  # Replace with your 16-character app password
)
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
                duration TEXT,
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
                mentor TEXT NOT NULL,
                duration TEXT,
                fees TEXT
            )
        ''')
    # Course Registrations Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS course_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER,
                user_id INTEGER,
                payment_status TEXT DEFAULT 'Paid',
                UNIQUE(course_id, user_id),
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    # Reviews Table
    conn.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                user_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                comment TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
    conn.commit()

    # Create default admin user
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', ('admin',))
    if not cursor.fetchone():
      conn.execute(
          'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
          ('admin', 'Admin123!', 'subhalakshmisubhi@gmail.com', 'admin'),
      )
      conn.commit()

    # Seed sample courses if empty
    cursor.execute('SELECT COUNT(*) FROM courses')
    if cursor.fetchone()[0] == 0:
      sample_courses = [
          ('Mastering Italian Pasta', 'Learn how to make authentic fresh pasta from scratch.', 'Chef Marco', '2 Weeks', '$49'),
          ('Bakery Essentials & Pastries', 'Perfect your baking skills with croissants and tarts.', 'Chef Chloe', '1 Week', '$39'),
          ('Healthy Plant-Based Cooking', 'Delicious, nutrient-dense vegan recipes for everyday life.', 'Chef Alex', '3 Days', '$29'),
      ]
      conn.executemany(
          'INSERT INTO courses (title, description, mentor, duration, fees) VALUES (?, ?, ?, ?, ?)',
          sample_courses,
      )
      conn.commit()


init_db()


# --- FORCED LOGIN ROOT ROUTE ---
@app.route('/')
def index():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    recipes = conn.execute('SELECT * FROM recipes LIMIT 6').fetchall()
  return render_template('index.html', recipes=recipes)


@app.route('/recipes')
def recipes():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    recipes = conn.execute('SELECT * FROM recipes').fetchall()
  return render_template('recipes.html', recipes=recipes)


@app.route('/recipe/<int:id>')
def recipe_detail(id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (id,)).fetchone()
    reviews = conn.execute(
        '''
            SELECT reviews.*, users.username FROM reviews 
            JOIN users ON reviews.user_id = users.id 
            WHERE recipe_id = ?
        ''',
        (id,),
    ).fetchall()
  return render_template('recipe_detail.html', recipe=recipe, reviews=reviews)


@app.route('/recipe/<int:id>/review', methods=['POST'])
def add_review(id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  rating = request.form.get('rating')
  comment = request.form.get('comment')

  if comment:
    with get_db_connection() as conn:
      conn.execute(
          'INSERT INTO reviews (recipe_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
          (id, session['user_id'], rating, comment),
      )
      conn.commit()

  return redirect(url_for('recipe_detail', id=id))


@app.route('/add', methods=['GET', 'POST'])
def add_recipe():
  if 'user_id' not in session:
    return redirect(url_for('login'))

  if request.method == 'POST':
    title = request.form.get('title')
    ingredients = request.form.get('ingredients')
    instructions = request.form.get('instructions')
    category = request.form.get('category')
    calories = request.form.get('calories') or 0
    duration = request.form.get('duration') or '30 mins'

    with get_db_connection() as conn:
      conn.execute(
          'INSERT INTO recipes (title, ingredients, instructions, category, calories, duration, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
          (title, ingredients, instructions, category, calories, duration, session['user_id']),
      )
      conn.commit()
    return redirect(url_for('recipes'))

  return render_template('add_recipe.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    recipe = conn.execute('SELECT * FROM recipes WHERE id = ?', (id,)).fetchone()

  if not recipe:
    return 'Recipe not found', 404

  if request.method == 'POST':
    title = request.form.get('title')
    ingredients = request.form.get('ingredients')
    instructions = request.form.get('instructions')
    category = request.form.get('category')
    calories = request.form.get('calories') or 0
    duration = request.form.get('duration') or '30 mins'

    with get_db_connection() as conn:
      conn.execute(
          'UPDATE recipes SET title = ?, ingredients = ?, instructions = ?, category = ?, calories = ?, duration = ? WHERE id = ?',
          (title, ingredients, instructions, category, calories, duration, id),
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
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    courses = conn.execute('SELECT * FROM courses').fetchall()
    registered_ids = []
    if 'user_id' in session:
      regs = conn.execute(
          'SELECT course_id FROM course_registrations WHERE user_id = ?',
          (session['user_id'],),
      ).fetchall()
      registered_ids = [r['course_id'] for r in regs]
  return render_template('courses.html', courses=courses, registered_ids=registered_ids)


@app.route('/course/pay/<int:course_id>', methods=['GET', 'POST'])
def course_pay(course_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  with get_db_connection() as conn:
    course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

  if not course:
    return 'Course not found', 404

  if request.method == 'POST':
    card_name = request.form.get('card_name')
    card_number = request.form.get('card_number')

    if card_name and card_number:
      try:
        with get_db_connection() as conn:
          conn.execute(
              'INSERT INTO course_registrations (course_id, user_id, payment_status) VALUES (?, ?, ?)',
              (course_id, session['user_id'], 'Paid'),
          )
          conn.commit()

          user = conn.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],)).fetchone()

        if user and user['email']:
          try:
            msg = Message(
                subject=f'Payment Confirmed & Registered for {course["title"]}!',
                recipients=[user['email']],
                body=f'Hi {user["username"]},\n\nYour payment of {course["fees"]} for the workshop "{course["title"]}" was successful!\nMentor: {course["mentor"]}\nDuration: {course["duration"]}\n\nWe look forward to seeing you there!\n\n- The Coco\'s Recipes Team'
            )
            mail.send(msg)
          except Exception as e:
            print(f'Workshop email dispatch failed: {e}')

        return redirect(url_for('courses'))
      except sqlite3.IntegrityError:
        return redirect(url_for('courses'))

  return render_template('payment.html', course=course)


@app.route('/course/unregister/<int:course_id>', methods=['POST'])
def unregister_course(course_id):
  if 'user_id' not in session:
    return redirect(url_for('login'))

  try:
    with get_db_connection() as conn:
      user = conn.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],)).fetchone()
      course = conn.execute('SELECT title FROM courses WHERE id = ?', (course_id,)).fetchone()

      conn.execute(
          'DELETE FROM course_registrations WHERE course_id = ? AND user_id = ?',
          (course_id, session['user_id'])
      )
      conn.commit()

    if user and user['email'] and course:
      try:
        msg = Message(
            subject=f'Registration Cancelled & Refund Processed for {course["title"]}',
            recipients=[user['email']],
            body=f'Hi {user["username"]},\n\nYour registration for the workshop "{course["title"]}" has been cancelled and your refund has been initiated.\n\nWe hope to see you in another workshop soon!\n\n- The Coco\'s Recipes Team'
        )
        mail.send(msg)
      except Exception as e:
        print(f'Cancellation email dispatch failed: {e}')

  except Exception as e:
    print(f'Unregistration failed: {e}')

  return redirect(url_for('courses'))


@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')

    if len(password) < 6 or not re.search(r'[A-Z]', password) or not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
      error_msg = 'Password must be longer than 5 characters, contain at least one uppercase letter, and at least one unique/special character (e.g. !@#$)'
      return render_template('register.html', error=error_msg)

    try:
      with get_db_connection() as conn:
        conn.execute(
            'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
            (username, password, email, 'user'),
        )
        conn.commit()

      if email:
        try:
          msg = Message(
              subject="Welcome to Coco's Recipes!",
              recipients=[email],
              body=f'Hi {username},\n\nThank you for registering on Coco\'s Recipes! Your account has been securely created.\n\nHappy cooking!\n- The Coco\'s Recipes Team'
          )
          mail.send(msg)
        except Exception as e:
          print(f'Email dispatch failed: {e}')

      return redirect(url_for('login'))
    except sqlite3.IntegrityError:
      return render_template('register.html', error='Username already exists!')

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
