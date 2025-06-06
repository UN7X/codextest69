import os
from flask import session
from . import app

@app.before_request
def ensure_session():
    if 'sid' not in session:
        session['sid'] = os.urandom(8).hex()
