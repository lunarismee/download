from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Thay bằng key bí mật thực tế

# Config Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Tạo database nếu chưa có
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY, name TEXT, path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fixes (id INTEGER PRIMARY KEY, title TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS guides (id INTEGER PRIMARY KEY, title TEXT, content TEXT)''')
    # Thêm admin mặc định nếu chưa có (username: admin, password: admin123)
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed_pw = generate_password_hash('admin123')
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))
    conn.commit()
    conn.close()

init_db()

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Trang login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            login_user(User(user[0]))
            return redirect(url_for('admin'))
        flash('Sai username hoặc password')
    return render_template('login.html')

# Trang logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Trang chính (frontend)
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM files")
    files = c.fetchall()
    c.execute("SELECT id, title, content FROM fixes")
    fixes = c.fetchall()
    c.execute("SELECT id, title, content FROM guides")
    guides = c.fetchall()
    conn.close()
    return render_template('index.html', files=files, fixes=fixes, guides=guides)

# Download file
@app.route('/download/<int:file_id>')
def download(file_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT name, path FROM files WHERE id=?", (file_id,))
    file = c.fetchone()
    conn.close()
    if file:
        return send_from_directory('uploads', file[0], as_attachment=True)
    return 'File không tồn tại'

# Trang admin
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_file':
            file = request.files['file']
            if file:
                filename = file.filename
                file.save(os.path.join('uploads', filename))
                c.execute("INSERT INTO files (name, path) VALUES (?, ?)", (filename, f'uploads/{filename}'))
        elif action == 'delete_file':
            file_id = request.form['file_id']
            c.execute("SELECT name FROM files WHERE id=?", (file_id,))
            filename = c.fetchone()[0]
            os.remove(os.path.join('uploads', filename))
            c.execute("DELETE FROM files WHERE id=?", (file_id,))
        elif action == 'add_fix':
            title = request.form['title']
            content = request.form['content']
            c.execute("INSERT INTO fixes (title, content) VALUES (?, ?)", (title, content))
        elif action == 'delete_fix':
            fix_id = request.form['fix_id']
            c.execute("DELETE FROM fixes WHERE id=?", (fix_id,))
        elif action == 'add_guide':
            title = request.form['title']
            content = request.form['content']
            c.execute("INSERT INTO guides (title, content) VALUES (?, ?)", (title, content))
        elif action == 'delete_guide':
            guide_id = request.form['guide_id']
            c.execute("DELETE FROM guides WHERE id=?", (guide_id,))
        conn.commit()
    c.execute("SELECT id, name FROM files")
    files = c.fetchall()
    c.execute("SELECT id, title, content FROM fixes")
    fixes = c.fetchall()
    c.execute("SELECT id, title, content FROM guides")
    guides = c.fetchall()
    conn.close()
    return render_template('admin.html', files=files, fixes=fixes, guides=guides)

# ... (toàn bộ code cũ của bạn giữ nguyên)

# Phần cuối file - bắt buộc cho Vercel
app = Flask(__name__)  # ← đảm bảo biến app là Flask instance

# Nếu bạn đã có app = Flask(__name__) ở trên thì bỏ dòng này đi

if __name__ == '__main__':
    app.run(debug=True)