import os
import io
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from app.utils import init_defaults

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
        init_defaults()
    yield client


def register(client, username, password):
    return client.post('/register', data={'username': username, 'password': password}, follow_redirects=True)


def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_register_login(client):
    rv = register(client, 'user', 'pass')
    assert b'Registered' in rv.data
    rv = login(client, 'user', 'pass')
    assert b'Welcome' in rv.data


def test_guest_upload_limit(client):
    data = {
        'file': (io.BytesIO(b'a' * (11 * 1024 * 1024)), 'big.txt')
    }
    rv = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'File too large' in rv.data


def test_user_upload_limit(client):
    register(client, 'user2', 'pass')
    login(client, 'user2', 'pass')
    data = {
        'file': (io.BytesIO(b'a' * (41 * 1024 * 1024)), 'big.txt')
    }
    rv = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert b'File too large' in rv.data
