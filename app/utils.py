import os
from flask import session
from werkzeug.security import generate_password_hash
from . import app, db
from .models import User

@app.before_request
def ensure_session():
    if 'sid' not in session:
        session['sid'] = os.urandom(8).hex()


def init_defaults():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin',
                         password=generate_password_hash('root'),
                         is_admin=True)
            db.session.add(admin)
            db.session.commit()
