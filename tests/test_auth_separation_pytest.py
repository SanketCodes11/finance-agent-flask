import pytest
from flask import url_for
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
def setup_users(app):
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', is_admin=True, is_active=True)
        admin.set_password('pass123')
        
        normal = User(username='normal', email='normal@test.com', is_admin=False, is_active=True)
        normal.set_password('pass123')
        
        db.session.add_all([admin, normal])
        db.session.commit()

def test_admin_on_normal_login_rejected(client, setup_users):
    res = client.post('/auth/login', data={'username': 'admin', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    # It should redirect to admin login and show the info message
    assert b'Administrator accounts must log in through the dedicated Super Admin Portal.' in res.data
    assert b'Super Admin Portal' in res.data
    
    # Verify the session is NOT active for the normal dashboard
    res2 = client.get('/dashboard')
    assert res2.status_code == 302
    assert b'/auth/login' in res2.data

def test_normal_on_normal_login_success(client, setup_users):
    res = client.post('/auth/login', data={'username': 'normal', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Finance Insight Agent' in res.data # Indicates main dashboard
    assert b'Super Admin Portal' not in res.data # Indicates NOT admin login

def test_normal_on_admin_login_rejected(client, setup_users):
    res = client.post('/admin/login', data={'username': 'normal', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Access Denied: Admin privileges required.' in res.data
    
    # Verify the session is NOT active for the normal dashboard
    res2 = client.get('/dashboard')
    assert res2.status_code == 302
    assert b'/auth/login' in res2.data

def test_admin_on_admin_login_success(client, setup_users):
    res = client.post('/admin/login', data={'username': 'admin', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Super Admin Dashboard' in res.data
