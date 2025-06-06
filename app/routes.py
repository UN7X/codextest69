import os
from datetime import datetime
from flask import render_template, redirect, url_for, request, flash, session, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from . import app, db, limiter
from .models import User, File, Paste

ALLOWED_EXTENSIONS = set(['txt', 'png', 'jpg', 'jpeg', 'gif', 'pdf'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    files = get_user_files()
    return render_template('index.html', files=files)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit('5/minute')
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash('Username exists')
        else:
            user = User(username=username, password=password)
            db.session.add(user)
            db.session.commit()
            flash('Registered, please login')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('10/minute')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
@limiter.limit('20/minute')
def upload():
    file = request.files.get('file')
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    if not allowed_file(file.filename):
        flash('File type not allowed')
        return redirect(url_for('index'))
    if current_user.is_authenticated:
        max_size = 40 * 1024 * 1024
    else:
        max_size = 10 * 1024 * 1024
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size:
        flash('File too large')
        return redirect(url_for('index'))
    filename = secure_filename(file.filename)
    stored = f"{datetime.utcnow().timestamp()}_{filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], stored)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(path)
    f = File(filename=filename, stored_name=stored)
    if current_user.is_authenticated:
        f.owner = current_user
    else:
        f.session_id = session.get('sid')
    db.session.add(f)
    db.session.commit()
    flash('Uploaded')
    return redirect(url_for('index'))

@app.route('/files/<name>')
def uploaded_file(name):
    return send_from_directory(app.config['UPLOAD_FOLDER'], name)

@app.route('/file/<int:file_id>/delete')
@login_required
def delete_file(file_id):
    f = File.query.get_or_404(file_id)
    if not can_access(f):
        flash('Access denied')
        return redirect(url_for('index'))
    db.session.delete(f)
    db.session.commit()
    flash('Deleted')
    return redirect(url_for('index'))

@app.route('/file/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    f = File.query.get_or_404(file_id)
    if not can_access(f):
        flash('Access denied')
        return redirect(url_for('index'))
    newname = request.form.get('name')
    if newname:
        f.filename = secure_filename(newname)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/file/<int:file_id>/expire', methods=['POST'])
@login_required
def set_expiration(file_id):
    f = File.query.get_or_404(file_id)
    if not can_access(f):
        flash('Access denied')
        return redirect(url_for('index'))
    date = request.form.get('expire')
    if date:
        f.expire_at = datetime.fromisoformat(date)
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/pastes')
def list_pastes():
    if current_user.is_authenticated:
        pastes = Paste.query.filter_by(user_id=current_user.id).all()
    else:
        pastes = Paste.query.filter_by(session_id=session.get('sid')).all()
    return render_template('pastes.html', pastes=pastes)

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Admin only')
        return redirect(url_for('index'))
    users = User.query.all()
    files = File.query.all()
    return render_template('admin.html', users=users, files=files)

def get_user_files():
    if current_user.is_authenticated:
        files = File.query.filter_by(user_id=current_user.id).all()
    else:
        sid = session.get('sid')
        files = File.query.filter_by(session_id=sid).all()
    return files

def can_access(file):
    return current_user.is_authenticated and (file.owner == current_user or current_user.is_admin)
