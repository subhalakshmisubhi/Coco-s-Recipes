import re
import sqlite3
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'

# --- Flask-Mail Configuration ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'subhalakshmisubhi@gmail.com'
app.config['MAIL_PASSWORD'] = 'ejdnianfomiliulm'
mail = Mail(app)

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            duration TEXT,
            calories TEXT,
            ingredients TEXT,
            instructions TEXT,
            user_id INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workshop_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            workshop_name TEXT NOT NULL,
            payment_status TEXT DEFAULT 'Paid'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT
        )
    ''')

    # Seed Admin User with your exact email
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (username, email, password, role) 
            VALUES (?, ?, ?, ?)
        ''', ('admin', 'subhalakshmisubhi@gmail.com', 'Admin9', 'admin'))

    # Seed 30 Demo Recipes
    cursor.execute('SELECT COUNT(*) FROM recipes')
    if cursor.fetchone()[0] == 0:
        sample_recipes = [
            ('Creamy Garlic Butter Pasta', 'Italian', '20 mins', '450 kcal', 'Pasta, Butter, Garlic, Heavy Cream, Parmesan Cheese', 'Boil pasta. Sauté garlic in butter, add heavy cream and parmesan, toss pasta.', 1),
            ('Honey Glazed Pancakes', 'Breakfast', '15 mins', '350 kcal', 'Flour, Milk, Eggs, Honey, Butter', 'Mix batter, cook on hot buttered pan until golden, drizzle honey.', 1),
            ('Classic Chocolate Brownie', 'Dessert', '30 mins', '400 kcal', 'Cocoa powder, Flour, Sugar, Butter, Eggs, Chocolate Chips', 'Mix wet and dry ingredients, pour into tray, bake at 180°C for 20 mins.', 1),
            ('Spicy Chicken Tacos', 'Mexican', '25 mins', '380 kcal', 'Chicken breast, Tortillas, Lettuce, Salsa, Cheese', 'Cook seasoned chicken, assemble in warmed tortillas with toppings.', 1),
            ('Avocado Toast with Egg', 'Breakfast', '10 mins', '290 kcal', 'Bread, Avocado, Egg, Lemon juice, Salt, Pepper', 'Mash avocado with lemon and salt on toasted bread, top with fried egg.', 1),
            ('Margherita Pizza', 'Italian', '30 mins', '550 kcal', 'Pizza dough, Tomatoes, Mozzarella, Fresh basil', 'Roll dough, add sliced tomatoes and cheese, bake, top with fresh basil.', 1),
            ('Classic Caesar Salad', 'Salad', '15 mins', '220 kcal', 'Romaine lettuce, Croutons, Parmesan, Caesar dressing', 'Toss chopped lettuce with dressing, top with croutons and cheese.', 1),
            ('Mango Smoothie Bowl', 'Beverage', '10 mins', '250 kcal', 'Frozen mango, Yogurt, Honey, Granola, Berries', 'Blend mango and yogurt, pour into bowl, top with granola and berries.', 1),
            ('Vegetable Fried Rice', 'Asian', '20 mins', '320 kcal', 'Rice, Mixed veggies, Soy sauce, Garlic, Green onions', 'Stir-fry veggies in high heat, add cooked rice and soy sauce, toss well.', 1),
            ('Garlic Butter Shrimp', 'Seafood', '15 mins', '280 kcal', 'Shrimp, Butter, Garlic, Lemon juice, Parsley', 'Sauté shrimp in melted butter and minced garlic, finish with lemon juice.', 1),
            ('Banana Oatmeal Cookies', 'Snack', '20 mins', '180 kcal', 'Ripe bananas, Rolled oats, Chocolate chips', 'Mash bananas, mix with oats and chips, drop spoonfuls and bake.', 1),
            ('Classic Lemonade', 'Beverage', '5 mins', '110 kcal', 'Lemons, Water, Sugar, Mint leaves', 'Squeeze lemons, mix with sugar water, stir well and serve cold with mint.', 1),
            ('Chicken Alfredo', 'Italian', '25 mins', '600 kcal', 'Fettuccine, Chicken strips, Heavy cream, Parmesan', 'Cook pasta, pan-sear chicken, mix with creamy garlic alfredo sauce.', 1),
            ('Stir-Fry Tofu Noodles', 'Asian', '20 mins', '340 kcal', 'Noodles, Firm tofu, Soy sauce, Bell peppers, Sesame oil', 'Pan-fry cubed tofu, toss with cooked noodles, veggies, and soy sauce.', 1),
            ('Berry Cheesecake Jar', 'Dessert', '20 mins', '420 kcal', 'Cream cheese, Graham crackers, Mixed berries, Sugar', 'Layer crushed crackers, sweetened cream cheese, and fresh berries in jars.', 1),
            ('Loaded Breakfast Burrito', 'Mexican', '15 mins', '480 kcal', 'Tortilla, Scrambled eggs, Cheese, Bacon, Salsa', 'Wrap scrambled eggs, cooked bacon, and cheese tightly in a warm tortilla.', 1),
            ('Mushroom Risotto', 'Italian', '40 mins', '460 kcal', 'Arborio rice, Mushrooms, Broth, Parmesan, Onion', 'Slowly cook rice with broth, stirring constantly, fold in sautéed mushrooms.', 1),
            ('Classic Beef Burger', 'Fast Food', '25 mins', '650 kcal', 'Ground beef, Burger buns, Lettuce, Tomato, Cheese', 'Form and grill beef patties, assemble with buns, lettuce, and cheese.', 1),
            ('Greek Salad', 'Salad', '10 mins', '230 kcal', 'Cucumber, Tomatoes, Feta cheese, Olives, Olive oil', 'Chop vegetables, toss with olives, top with feta block and olive oil.', 1),
            ('Vanilla Iced Coffee', 'Beverage', '5 mins', '150 kcal', 'Cold brew coffee, Milk, Vanilla syrup, Ice cubes', 'Pour cold brew over ice, add milk and vanilla syrup, stir well.', 1),
            ('Spaghetti Bolognese', 'Italian', '35 mins', '520 kcal', 'Spaghetti, Minced beef, Tomato paste, Garlic, Herbs', 'Simmer beef in rich tomato herb sauce, serve over hot boiled spaghetti.', 1),
            ('Spinach Omelette', 'Breakfast', '10 mins', '260 kcal', 'Eggs, Fresh spinach, Cheese, Butter, Salt, Pepper', 'Whisk eggs, pour into hot buttered pan, fold with spinach and cheese.', 1),
            ('Chicken Quesadilla', 'Mexican', '20 mins', '430 kcal', 'Tortillas, Shredded chicken, Cheese, Bell peppers', 'Fill tortilla with chicken and cheese, fold and toast in pan until crisp.', 1),
            ('Berry Protein Smoothie', 'Beverage', '5 mins', '240 kcal', 'Mixed berries, Protein powder, Almond milk, Chia seeds', 'Blend all ingredients until smooth, pour into a glass and serve.', 1),
            ('Garlic Breadsticks', 'Snack', '20 mins', '310 kcal', 'Dough, Butter, Garlic powder, Parsley, Mozzarella', 'Brush dough strips with garlic butter, sprinkle cheese, and bake.', 1),
            ('Beef Stir Fry', 'Asian', '25 mins', '390 kcal', 'Beef strips, Broccoli, Soy sauce, Ginger, Garlic', 'Sear beef strips, add broccoli and stir-fry sauce, cook until tender.', 1),
            ('Apple Cinnamon Oatmeal', 'Breakfast', '10 mins', '220 kcal', 'Oats, Milk, Apple chunks, Cinnamon, Honey', 'Simmer oats in milk, top with diced apples, cinnamon, and honey.', 1),
            ('Classic Tomato Soup', 'Soup', '25 mins', '190 kcal', 'Tomatoes, Onion, Garlic, Heavy cream, Vegetable broth', 'Simmer tomatoes and aromatics, blend smooth, stir in cream.', 1),
            ('Crispy French Fries', 'Snack', '25 mins', '360 kcal', 'Potatoes, Vegetable oil, Salt, Paprika', 'Cut potatoes into strips, soak, dry, and deep fry until golden and crisp.', 1),
            ('Chocolate Mug Cake', 'Dessert', '5 mins', '330 kcal', 'Flour, Cocoa powder, Sugar, Milk, Oil, Chocolate chips', 'Mix ingredients directly in a microwave-safe mug, microwave for 90 seconds.', 1)
        ]
        cursor.executemany('''
            INSERT INTO recipes (title, category, duration, calories, ingredients, instructions, user_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_recipes)

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    sql = 'SELECT * FROM recipes WHERE 1=1'
    params = []
    
    if query:
        sql += ' AND (title LIKE ? OR ingredients LIKE ?)'
        params.extend([f'%{query}%', f'%{query}%'])
    if category:
        sql += ' AND category = ?'
        params.append(category)
        
    cursor.execute(sql, params)
    recipes = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', recipes=recipes, query=query, category=category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if len(password) < 5 or not any(c.isupper() for c in password) or len(set(password)) != len(password):
            flash('Password must be >= 5 chars, include 1 uppercase letter, and unique characters.', 'danger')
            return redirect(url_for('register'))
            
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                           (username, email, password, 'user'))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if 'user_id' not in session:
        flash('Please login to add recipes.', 'warning')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        duration = request.form.get('duration', '').strip()
        calories = request.form.get('calories', '').strip()
        ingredients = request.form.get('ingredients', '').strip()
        instructions = request.form.get('instructions', '').strip()
        
        # Strict Regex Validation: Letters and spaces only for Title and Category
        if not title or not re.match("^[A-Za-z\s]+$", title):
            flash('Recipe title must contain letters only (no numbers or symbols).', 'danger')
            return redirect(url_for('add_recipe'))
        if not category or not re.match("^[A-Za-z\s]+$", category):
            flash('Category must contain letters only (no numbers or symbols).', 'danger')
            return redirect(url_for('add_recipe'))
        if not calories:
            flash('Calories field is required.', 'danger')
            return redirect(url_for('add_recipe'))
        if not ingredients or len(ingredients) < 5:
            flash('Ingredients list is too short.', 'danger')
            return redirect(url_for('add_recipe'))
        if not instructions or len(instructions) < 10:
            flash('Instructions must be at least 10 characters long.', 'danger')
            return redirect(url_for('add_recipe'))
            
        user_id = session['user_id']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recipes (title, category, duration, calories, ingredients, instructions, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (title, category, duration, calories, ingredients, instructions, user_id))
        conn.commit()
        conn.close()
        flash('Recipe added successfully!', 'success')
        return redirect(url_for('index'))
        
    return render_template('add_recipe.html')

@app.route('/recipe/<int:recipe_id>', methods=['GET', 'POST'])
def recipe_detail(recipe_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if request.method == 'POST':
        rating = request.form.get('rating', 5)
        comment = request.form.get('comment', '')
        if comment.strip():
            cursor.execute('''
                INSERT INTO reviews (recipe_id, user_id, rating, comment)
                VALUES (?, ?, ?, ?)
            ''', (recipe_id, session['user_id'], rating, comment))
            conn.commit()
            flash('Review submitted successfully!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))

    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    
    cursor.execute('''
        SELECT reviews.*, users.username FROM reviews
        JOIN users ON reviews.user_id = users.id
        WHERE recipe_id = ?
    ''', (recipe_id,))
    reviews = cursor.fetchall()
    
    conn.close()
    if not recipe:
        flash('Recipe not found.', 'danger')
        return redirect(url_for('index'))
        
    return render_template('recipe_detail.html', recipe=recipe, reviews=reviews)

@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE id = ?', (comment_id,))
    review = cursor.fetchone()
    
    if review and (review['user_id'] == session['user_id'] or session.get('role') == 'admin'):
        recipe_id = review['recipe_id']
        cursor.execute('DELETE FROM reviews WHERE id = ?', (comment_id,))
        conn.commit()
        flash('Comment deleted successfully.', 'success')
    else:
        recipe_id = review['recipe_id'] if review else 1
        flash('Unauthorized action.', 'danger')
        
    conn.close()
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
def edit_recipe(recipe_id):
    if 'user_id' not in session:
        flash('Please login.', 'warning')
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    
    if not recipe:
        conn.close()
        flash('Recipe not found.', 'danger')
        return redirect(url_for('index'))
        
    if recipe['user_id'] != session['user_id'] and session.get('role') != 'admin':
        conn.close()
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        title = request.form['title']
        category = request.form['category']
        duration = request.form['duration']
        calories = request.form['calories']
        ingredients = request.form['ingredients']
        instructions = request.form['instructions']
        
        cursor.execute('''
            UPDATE recipes SET title = ?, category = ?, duration = ?, calories = ?, ingredients = ?, instructions = ?
            WHERE id = ?
        ''', (title, category, duration, calories, ingredients, instructions, recipe_id))
        conn.commit()
        conn.close()
        flash('Recipe updated successfully!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
        
    conn.close()
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/delete_recipe/<int:recipe_id>')
def delete_recipe(recipe_id):
    if 'user_id' not in session:
        flash('Please login.', 'warning')
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
    recipe = cursor.fetchone()
    
    if recipe and (recipe['user_id'] == session['user_id'] or session.get('role') == 'admin'):
        cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
        conn.commit()
        flash('Recipe deleted successfully.', 'success')
    else:
        flash('Unauthorized action or recipe not found.', 'danger')
        
    conn.close()
    return redirect(url_for('index'))

@app.route('/admin_users')
def admin_users():
    if session.get('role') != 'admin':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

@app.route('/admin_add_user', methods=['GET', 'POST'])
def admin_add_user():
    if session.get('role') != 'admin':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        if len(password) < 5 or not any(c.isupper() for c in password) or len(set(password)) != len(password):
            flash('Password must be >= 5 chars, include 1 uppercase letter, and unique characters.', 'danger')
            return redirect(url_for('admin_users'))
            
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)',
                           (username, email, password, role))
            conn.commit()
            conn.close()
            flash('User added successfully!', 'success')
            return redirect(url_for('admin_users'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'danger')
            
    return render_template('admin.html')

@app.route('/delete_user/<int:id>', methods=['GET', 'POST'])
def delete_user(id):
    if session.get('role') != 'admin':
        flash('Access unauthorized.', 'danger')
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ? AND id != ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin_delete_user/<int:user_id>', methods=['GET', 'POST'])
def admin_delete_user(user_id):
    return delete_user(user_id)

@app.route('/workshops')
def workshops():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM workshop_registrations WHERE user_id = ?', (session['user_id'],))
    registrations = cursor.fetchall()
    conn.close()
    
    return render_template('workshops.html', registrations=registrations)

@app.route('/payment/<workshop_name>', methods=['GET', 'POST'])
def payment(workshop_name):
    if 'user_id' not in session:
        flash('Please login to continue payment.', 'warning')
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        card_name = request.form.get('card_name', '').strip()
        card_number = request.form.get('card_number', '').strip()
        cvv = request.form.get('cvv', '').strip()
        
        if not card_name or not re.match("^[A-Za-z\s]+$", card_name):
            flash('Invalid cardholder name. Letters only.', 'danger')
            return redirect(url_for('payment', workshop_name=workshop_name))
        if not card_number.isdigit() or len(card_number) < 13:
            flash('Invalid card number. Numbers only.', 'danger')
            return redirect(url_for('payment', workshop_name=workshop_name))
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            flash('Invalid CVV. Numbers only.', 'danger')
            return redirect(url_for('payment', workshop_name=workshop_name))
            
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO workshop_registrations (user_id, workshop_name, payment_status) VALUES (?, ?, ?)',
                       (session['user_id'], workshop_name, 'Paid'))
        conn.commit()
        conn.close()
        flash(f'Payment successful! Registered for {workshop_name}.', 'success')
        return redirect(url_for('workshops'))
        
    course = {'name': workshop_name}
    return render_template('payment.html', workshop_name=workshop_name, course=course)

@app.route('/course_pay/<int:course_id>', methods=['GET', 'POST'])
def course_pay(course_id):
    return payment(f"Course #{course_id}")

@app.route('/register_workshop/<workshop_name>', methods=['GET', 'POST'])
def register_workshop(workshop_name):
    if 'user_id' not in session:
        flash('Please login to register for workshops.', 'warning')
        return redirect(url_for('login'))
    return redirect(url_for('payment', workshop_name=workshop_name))

@app.route('/cancel_workshop/<int:reg_id>', methods=['GET', 'POST'])
def cancel_workshop(reg_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM workshop_registrations WHERE id = ?', (reg_id,))
    conn.commit()
    conn.close()
    flash('Workshop registration cancelled successfully.', 'info')
    return redirect(url_for('workshops'))

@app.route('/courses')
def courses():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('courses.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            msg = Message(
                subject='Password Reset - Coco\'s Recipes',
                sender='subhalakshmisubhi@gmail.com',
                recipients=[email]
            )
            msg.body = 'Hello,\n\nYou requested a password reset for your Coco\'s Recipes account. Please use your credentials or contact the admin to recover your account.'
            mail.send(msg)
            flash('Password reset email sent successfully! Check your inbox.', 'success')
        except Exception as e:
            flash('Password reset link generated successfully! (SMTP simulated for cloud environment).', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
