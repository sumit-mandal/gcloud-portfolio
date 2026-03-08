import os
import sqlite3
import uuid
import hashlib
import secrets
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    session, redirect, url_for
)
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env'))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'portfolio.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Default admin credentials — change via env vars in production
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS_HASH = hashlib.sha256(
    os.environ.get('ADMIN_PASS', 'admin123').encode()
).hexdigest()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            display_order INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        );
    ''')
    conn.commit()
    count = conn.execute('SELECT COUNT(*) FROM sections').fetchone()[0]
    if count == 0:
        seed_data(conn)
    conn.close()


def seed_data(conn):
    entries = [
        ("Kashmir", "Kashmir was one of the best places I've been into. I went there in mid decembers witnessed snowfall over there. Phalgam, gulmarg, doodhpathri and srinagar were one of the few places where I paid visit.", ["photo1.jpg"]),
        ("Jodhpur", "Jodhpur also known as blue city was really mesmerizing, visited there during monsoon. The sunset was really amazing at jodhpur. The place is really peacefull. The place has rich history.", ["photo2.jpg"]),
        ("Amritsar", "Amritsar was an incredible experience, offering rich history and beautiful sights. The Golden Temple and local culture left a lasting impression.", ["photo3.jpg", "photo4.jpg"]),
        ("Snowy, Milo and Buki", "Three stray cats came into our lives, filling our home with immense joy and love. Though their time with us was heartbreakingly short, they brought us more happiness than we ever imagined. Sadly, illness took them before they could even reach one year, despite our best efforts to save them. Their love will remain in our hearts forever.", ["photo5.jpg"]),
        ("DIU", "The trip to Diu was a refreshing getaway, filled with scenic views and tranquil beaches. The blend of culture and nature made for a memorable experience.", ["photo6.jpg"]),
        ("Mumbai", "The city of dreams has a lot to offer. The place is a perfect combination of Hustle-Bustle and peace.", ["photo7.jpg"]),
        ("Goa", "Goa's beaches and vibrant nightlife made for an unforgettable trip. The mix of relaxation and adventure was perfect.", ["photo8.jpg", "photo9.jpg"]),
        ("Mussoorie", "The queen of hills Mussoorie is not just beautiful but the air is really serene, witnessed amazing rainbow at george everest peak. Did 2 hours of hiking to reach the hill top, and it was really worth it.", ["photo10.jpg"]),
        ("Jaisalmer", "Got a chance to stay at the fort in Jaisalmer, this place is one of my favorites, serene breeze, warm deserts, delicious foods and most importantly great hospitality by the people. I did spend one night under open stars in the sand dunes, and the Place was no less than comfort.", ["photo12.jpg"]),
        ("Jaipur", "The pink city has a lots of amazing places with lots and lots of forts and amazing food. The place is a perfect mix of rich heritage, preserved culture and modern lifestyle. Visited nargarh fort, amer fort and jaigarh fort. Hawa mahal and pink city are must go place for any one who comes here and I was no exception.", ["photo13.jpg"]),
    ]
    for i, (title, desc, photos) in enumerate(entries):
        cursor = conn.execute(
            'INSERT INTO sections (title, description, display_order) VALUES (?, ?, ?)',
            (title, desc, i)
        )
        section_id = cursor.lastrowid
        for photo in photos:
            conn.execute(
                'INSERT INTO images (section_id, filename) VALUES (?, ?)',
                (section_id, photo)
            )
    conn.commit()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_image_url(filename):
    if os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
        return f'/static/uploads/{filename}'
    return f'/static/images/{filename}'


def load_sections():
    conn = get_db()
    sections = conn.execute('SELECT * FROM sections ORDER BY display_order, id').fetchall()
    result = []
    for section in sections:
        images = conn.execute('SELECT * FROM images WHERE section_id = ?', (section['id'],)).fetchall()
        result.append({
            'id': section['id'],
            'title': section['title'],
            'description': section['description'],
            'images': [{'id': img['id'], 'url': get_image_url(img['filename']), 'filename': img['filename']} for img in images]
        })
    conn.close()
    return result


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            if request.is_json or request.content_type and 'multipart' in request.content_type:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── Public Routes ──

@app.route('/')
def index():
    return render_template('index.html', sections=load_sections())


# ── Admin Auth ──

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('admin_panel'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        if username == ADMIN_USER and pass_hash == ADMIN_PASS_HASH:
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        error = 'Invalid credentials'
    return render_template('admin_login.html', error=error)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))


# ── Admin Panel ──

@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html', sections=load_sections())


# ── API (admin-protected) ──

@app.route('/api/sections', methods=['POST'])
@admin_required
def create_section():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    conn = get_db()
    max_order = conn.execute('SELECT COALESCE(MAX(display_order), -1) FROM sections').fetchone()[0]
    cursor = conn.execute(
        'INSERT INTO sections (title, description, display_order) VALUES (?, ?, ?)',
        (title, description, max_order + 1)
    )
    section_id = cursor.lastrowid

    uploaded_images = []
    for file in request.files.getlist('images'):
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            conn.execute('INSERT INTO images (section_id, filename) VALUES (?, ?)', (section_id, filename))
            img_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            uploaded_images.append({'id': img_id, 'url': f'/static/uploads/{filename}', 'filename': filename})

    conn.commit()
    conn.close()
    return jsonify({'id': section_id, 'title': title, 'description': description, 'images': uploaded_images}), 201


@app.route('/api/sections/<int:section_id>', methods=['PUT'])
@admin_required
def update_section(section_id):
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    conn = get_db()
    section = conn.execute('SELECT * FROM sections WHERE id = ?', (section_id,)).fetchone()
    if not section:
        conn.close()
        return jsonify({'error': 'Section not found'}), 404

    conn.execute('UPDATE sections SET title = ?, description = ? WHERE id = ?', (title, description, section_id))

    for file in request.files.getlist('images'):
        if file and file.filename and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4().hex}.{ext}"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            conn.execute('INSERT INTO images (section_id, filename) VALUES (?, ?)', (section_id, filename))

    conn.commit()
    all_images = conn.execute('SELECT * FROM images WHERE section_id = ?', (section_id,)).fetchall()
    conn.close()

    return jsonify({
        'id': section_id, 'title': title, 'description': description,
        'images': [{'id': img['id'], 'url': get_image_url(img['filename']), 'filename': img['filename']} for img in all_images]
    })


@app.route('/api/sections/<int:section_id>', methods=['DELETE'])
@admin_required
def delete_section(section_id):
    conn = get_db()
    section = conn.execute('SELECT * FROM sections WHERE id = ?', (section_id,)).fetchone()
    if not section:
        conn.close()
        return jsonify({'error': 'Section not found'}), 404

    images = conn.execute('SELECT * FROM images WHERE section_id = ?', (section_id,)).fetchall()
    for img in images:
        filepath = os.path.join(UPLOAD_FOLDER, img['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)

    conn.execute('DELETE FROM sections WHERE id = ?', (section_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Section deleted'}), 200


@app.route('/api/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_image(image_id):
    conn = get_db()
    image = conn.execute('SELECT * FROM images WHERE id = ?', (image_id,)).fetchone()
    if not image:
        conn.close()
        return jsonify({'error': 'Image not found'}), 404

    filepath = os.path.join(UPLOAD_FOLDER, image['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)

    conn.execute('DELETE FROM images WHERE id = ?', (image_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Image deleted'}), 200


init_db()

if __name__ == "__main__":
    app.run(debug=True)
