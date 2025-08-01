import sqlite3
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'simple_key_123'  # Simple key for development
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def init_db():
    conn = None
    try:
        os.makedirs('static/images', exist_ok=True)
        logging.info("Ensured static/images/ directory exists.")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            items TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payment_method TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        ''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            feedback TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')

        admin_username = 'admin'
        admin_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        c.execute("INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)",
                  (admin_username, admin_password))
        logging.info("Inserted default admin.")

        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            user_passwords = [generate_password_hash(f'password{i}', method='pbkdf2:sha256') for i in range(1, 6)]
            default_users = [
                ('shraddha', user_passwords[0], 'Shraddha', 'Chowdhury', 'shraddha@example.com'),
                ('aarav', user_passwords[1], 'Aarav', 'Roy', 'aarav@example.com'),
                ('ishaan', user_passwords[2], 'Ishaan', 'Gupta', 'ishaan@example.com'),
                ('aarshi', user_passwords[3], 'Aarshi', 'Banerjee', 'aarshi@example.com'),
                ('anik', user_passwords[4], 'Anik', 'Sen', 'anik@example.com')
            ]
            c.executemany("INSERT INTO users (username, password, first_name, last_name, email) VALUES (?, ?, ?, ?, ?)", default_users)
            logging.info("Inserted 5 default users.")

        c.execute("SELECT COUNT(*) FROM menu_items")
        if c.fetchone()[0] == 0:
            default_items = [
                ('Hot Cappuccino', 'Steaming hot cappuccino with frothy milk', 3.50, 'Hot Beverages', 'images/hot-beverages.png', 1),
                ('Iced Latte', 'Creamy and frothy cold latte', 4.00, 'Cold Beverages', 'images/cold-beverages.png', 1),
                ('Mango Smoothie', 'Refreshing mango-flavored smoothie', 4.50, 'Refreshment', 'images/refreshment.png', 1),
                ('Combo Meal', 'Cappuccino with a croissant', 6.00, 'Special Combo', 'images/special-combo.png', 1),
                ('Chocolate Cake', 'Rich chocolate layered cake', 5.00, 'Desserts', 'images/desserts.png', 1),
                ('Cheese Burger', 'Burger with fries', 7.00, 'Burger & Frenchfries', 'images/burger-frenchfries.png', 1)
            ]
            c.executemany("INSERT INTO menu_items (name, description, price, category, image, available) VALUES (?, ?, ?, ?, ?, ?)", default_items)
            logging.info("Inserted 6 default menu items.")

        c.execute("SELECT COUNT(*) FROM testimonials")
        if c.fetchone()[0] == 0:
            default_testimonials = [
                (1, 'Shraddha Chowdhury', 'Loved the French roast. Perfectly balanced and rich. Will order again!', 'images/user-1.jpg', '2025-06-27 16:34:00'),
                (2, 'Aarav Roy', 'Great espresso blend! Smooth and bold flavor. Fast shipping too!', 'images/user-2.jpg', '2025-06-27 16:34:00'),
                (3, 'Ishaan Gupta', 'Fantastic mocha flavor. Fresh and aromatic. Quick shipping!', 'images/user-3.jpg', '2025-06-27 16:34:00'),
                (4, 'Aarshi Banerjee', 'Excellent quality! Fresh beans and quick delivery. Highly recommend', 'images/user-4.jpg', '2025-06-27 16:34:00'),
                (5, 'Anik Sen', 'Best decaf I’ve tried! Smooth and flavorful. Arrived promptly.', 'images/user-5.jpg', '2025-06-27 16:34:00')
            ]
            c.executemany("INSERT INTO testimonials (user_id, name, feedback, image_url, created_at) VALUES (?, ?, ?, ?, ?)", default_testimonials)
            logging.info("Inserted 5 default testimonials.")

        conn.commit()

        c.execute("SELECT name, feedback, image_url FROM testimonials")
        testimonials = c.fetchall()
        logging.info(f"Verified {len(testimonials)} testimonials: {testimonials}")

        c.execute("SELECT username, first_name, email FROM users")
        users = c.fetchall()
        logging.info(f"Verified {len(users)} users: {users}")

        c.execute("SELECT name, category, image FROM menu_items")
        menu_items = c.fetchall()
        logging.info(f"Verified {len(menu_items)} menu items: {menu_items}")

        c.execute("SELECT username FROM admins")
        admins = c.fetchall()
        logging.info(f"Verified {len(admins)} admins: {admins}")

    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed.")

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    first_name = None
    testimonials = []
    
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if c.fetchone():
            if 'user_id' in session:
                c.execute("SELECT first_name FROM users WHERE id = ?", (session['user_id'],))
                user = c.fetchone()
                first_name = user['first_name'] if user else None
                logging.debug(f"User first_name: {first_name}")
        else:
            logging.warning("Users table does not exist.")
        
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='testimonials'")
        if c.fetchone():
            c.execute("SELECT name, feedback, image_url FROM testimonials")
            testimonials = [
                {
                    'name': row['name'],
                    'feedback': row['feedback'],
                    'image_url': row['image_url'] if row['image_url'] and os.path.exists(os.path.join('static', row['image_url'])) else 'images/placeholder.jpg'
                } for row in c.fetchall()
            ]
            logging.debug(f"Fetched {len(testimonials)} testimonials: {testimonials}")
            for t in testimonials:
                logging.debug(f"Checking image: static/{t['image_url']} exists: {os.path.exists(os.path.join('static', t['image_url']))}")
        else:
            logging.warning("Testimonials table does not exist.")
        
        conn.close()
    
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        testimonials = []
    
    return render_template('index.html', first_name=first_name, testimonials=testimonials)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def user_page():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT first_name FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return render_template('user_page.html', first_name=user[0] if user else None)

@app.route('/menu', methods=['GET', 'POST'])
@login_required
def menu():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name, description, price, category, image, available FROM menu_items WHERE available = 1")
    menu_items = c.fetchall()
    categories = sorted(set(item[4] for item in menu_items))
    items_by_category = {category: [item for item in menu_items if item[4] == category] for category in categories}
    conn.close()
    
    if request.method == 'POST':
        order_items = []
        total_price = 0.0
        for item_id in request.form:
            if item_id.startswith('quantity_'):
                item_id_num = item_id.replace('quantity_', '')
                quantity = int(request.form[item_id])
                if quantity > 0:
                    conn = sqlite3.connect('database.db')
                    c = conn.cursor()
                    c.execute("SELECT id, name, price FROM menu_items WHERE id = ? AND available = 1", (item_id_num,))
                    item = c.fetchone()
                    conn.close()
                    if item:
                        item_total = item[2] * quantity
                        total_price += item_total
                        order_items.append({
                            'id': item[0],
                            'name': item[1],
                            'quantity': quantity,
                            'price': item[2]
                        })
        if order_items:
            items_json = json.dumps(order_items)
            payment_method = request.form.get('payment_method', 'Pending')
            print(f"Storing order: user_id={session['user_id']}, items={items_json}, total={total_price}, payment_method={payment_method}")
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO orders (user_id, items, total_price, status, created_at, payment_method) VALUES (?, ?, ?, ?, ?, ?)",
                      (session['user_id'], items_json, total_price, 'Pending', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), payment_method))
            order_id = c.lastrowid
            conn.commit()
            conn.close()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_confirmation', order_id=order_id))
        else:
            flash('Please select at least one item to order.', 'error')
    
    return render_template('menu.html', items_by_category=items_by_category)

@app.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, items, total_price, status, created_at, payment_method FROM orders WHERE id = ? AND user_id = ?",
              (order_id, session['user_id']))
    order = c.fetchone()
    conn.close()
    if order:
        try:
            items = json.loads(order[1]) if order[1] else []
            order_details = {
                'id': order[0],
                'items': items,
                'total_price': order[2],
                'status': order[3],
                'created_at': order[4],
                'payment_method': order[5]
            }
            print(f"Rendering order_details: {order_details}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}, raw items={order[1]}")
            items = []
            flash('Error processing order items. Please contact support.', 'error')
            order_details = {
                'id': order[0],
                'items': items,
                'total_price': order[2],
                'status': order[3],
                'created_at': order[4],
                'payment_method': order[5]
            }
        return render_template('order_confirmation.html', order=order_details)
    flash('No such order found.', 'error')
    return redirect(url_for('menu'))

@app.route('/order_history')
@login_required
def order_history():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, items, total_price, status, created_at, payment_method FROM orders WHERE user_id = ? ORDER BY created_at DESC",
              (session['user_id'],))
    orders = c.fetchall()
    conn.close()
    order_history = []
    for order in orders:
        try:
            items = json.loads(order[1]) if order[1] else []
        except json.JSONDecodeError:
            items = []
        order_history.append({
            'id': order[0],
            'items': items,
            'total_price': order[2],
            'status': order[3],
            'created_at': order[4],
            'payment_method': order[5]
        })
    return render_template('order_history.html', orders=order_history)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, first_name, last_name, email) VALUES (?, ?, ?, ?, ?)",
                      (username, hashed_password, first_name, last_name, email))
            conn.commit()
            flash('Sign-up successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            error = 'Username or email already exists'
        finally:
            conn.close()
    return render_template('signup.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('user_page'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin_id', None)
    return redirect(url_for('login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM admins WHERE username = ?", (username,))
        admin = c.fetchone()
        conn.close()
        
        if admin and check_password_hash(admin[2], password):
            session['admin_id'] = admin[0]
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid admin username or password'
    return render_template('admin_login.html', error=error)

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute("SELECT id, name, description, price, category, image, available FROM menu_items")
    menu_items = c.fetchall()
    menu_items = [{
        'id': item[0],
        'name': item[1],
        'description': item[2],
        'price': item[3],
        'category': item[4],
        'image': item[5],
        'available': item[6]
    } for item in menu_items]
    
    c.execute("SELECT o.id, o.user_id, o.items, o.total_price, o.status, o.created_at, o.payment_method, u.username FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.created_at DESC")
    orders = c.fetchall()
    orders_data = [{
        'id': order[0],
        'user_id': order[1],
        'items': json.loads(order[2]) if order[2] else [],
        'total_price': order[3],
        'status': order[4],
        'created_at': order[5],
        'payment_method': order[6],
        'username': order[7]
    } for order in orders]
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_item':
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            category = request.form.get('category')
            image_file = request.files.get('image')
            if not all([name, description, price, category, image_file]):
                flash('All fields are required.', 'error')
            elif not allowed_file(image_file.filename):
                flash('Invalid image format. Use PNG, JPG, JPEG, or GIF.', 'error')
            else:
                try:
                    price = float(price)
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image_file.save(image_path)
                    c.execute("""
                        INSERT INTO menu_items (name, description, price, category, image, available)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, description, price, category, f'images/{filename}', 1))
                    conn.commit()
                    flash('Menu item added successfully!', 'success')
                except ValueError:
                    flash('Price must be a valid number.', 'error')
                except Exception as e:
                    flash(f'Error adding item: {str(e)}', 'error')
        elif action == 'remove_item':
            item_id = request.form.get('item_id')
            try:
                c.execute("UPDATE menu_items SET available = 0 WHERE id = ?", (item_id,))
                conn.commit()
                flash('Menu item removed successfully!', 'success')
            except Exception as e:
                flash(f'Error removing item: {str(e)}', 'error')
        elif action == 'update_order_status':
            order_id = request.form.get('order_id')
            status = request.form.get('status')
            try:
                c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
                conn.commit()
                flash('Order status updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating order status: {str(e)}', 'error')
        elif action == 'edit_item':
            item_id = request.form.get('item_id')
            name = request.form.get('name')
            description = request.form.get('description')
            price = request.form.get('price')
            category = request.form.get('category')
            image_file = request.files.get('image')
            
            if not all([item_id, name, description, price, category]):
                flash('All fields are required.', 'error')
            else:
                try:
                    price = float(price)
                    if image_file and allowed_file(image_file.filename):
                        filename = secure_filename(image_file.filename)
                        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        image_file.save(image_path)
                        image_update = f'images/{filename}'
                    else:
                        c.execute("SELECT image FROM menu_items WHERE id = ?", (item_id,))
                        image_update = c.fetchone()[0]
                    
                    c.execute("""
                        UPDATE menu_items
                        SET name = ?, description = ?, price = ?, category = ?, image = ?
                        WHERE id = ?
                    """, (name, description, price, category, image_update, item_id))
                    conn.commit()
                    flash('Menu item updated successfully!', 'success')
                except ValueError:
                    flash('Price must be a valid number.', 'error')
                except Exception as e:
                    flash(f'Error updating item: {str(e)}', 'error')
    
    conn.close()
    return render_template('admin_dashboard.html', menu_items=menu_items, orders=orders_data)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)