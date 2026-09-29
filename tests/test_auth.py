import os
import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Finance Insight Agent' in response.data

def test_register(client, app):
    response = client.post('/auth/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Password123',
        'password_confirm': 'Password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'

def test_login(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()

    response = client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'Password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Welcome back, testuser' in response.data or b'Dashboard' in response.data

def test_dashboard_unauthorized(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Please log in to access this page' in response.data
