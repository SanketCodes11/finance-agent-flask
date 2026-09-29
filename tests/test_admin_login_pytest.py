import pytest
from flask import session
from app import create_app, db
from app.models.user import User, AdminAuditLog
from app.models.finance import LoginHistory
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
        
        inactive_admin = User(username='badadmin', email='bad@test.com', is_admin=True, is_active=False)
        inactive_admin.set_password('pass123')
        
        normal = User(username='normal', email='normal@test.com', is_admin=False, is_active=True)
        normal.set_password('pass123')
        
        db.session.add_all([admin, inactive_admin, normal])
        db.session.commit()

def test_admin_login_success(client, setup_users, app):
    res = client.post('/admin/login', data={'username': 'admin', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Super Admin Dashboard' in res.data
    
    with app.app_context():
        # Check login history and admin log
        u = User.query.filter_by(username='admin').first()
        lh = LoginHistory.query.filter_by(user_id=u.id).first()
        al = AdminAuditLog.query.filter_by(admin_id=u.id, action='admin_login').first()
        assert lh is not None
        assert al is not None

def test_admin_login_invalid_password(client, setup_users):
    res = client.post('/admin/login', data={'username': 'admin', 'password': 'wrong'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Invalid username or password' in res.data
    # Ensure they are on the login page still
    assert b'Super Admin Portal' in res.data

def test_admin_login_normal_user_denied(client, setup_users, app):
    res = client.post('/admin/login', data={'username': 'normal', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Access Denied: Admin privileges required.' in res.data
    assert b'Super Admin Portal' in res.data
    
    # Prove they are NOT logged in
    res2 = client.get('/dashboard') # Normal user dashboard
    # Should redirect to normal login
    assert res2.status_code == 302
    assert b'/auth/login' in res2.data

def test_admin_login_inactive_admin_denied(client, setup_users):
    res = client.post('/admin/login', data={'username': 'badadmin', 'password': 'pass123'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Access Denied: Admin privileges required.' in res.data

def test_admin_login_open_redirect_prevention(client, setup_users):
    res = client.post('/admin/login?next=http://evil.com', data={'username': 'admin', 'password': 'pass123'})
    assert res.status_code == 302
    # Should safely fallback to admin.dashboard instead of evil.com
    assert '/admin/dashboard' in res.location
    assert 'http://evil.com' not in res.location

def test_admin_logout(client, setup_users):
    client.post('/admin/login', data={'username': 'admin', 'password': 'pass123'})
    res = client.get('/auth/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'Finance Insight Agent' in res.data # Should redirect back to main index
    
    # Verify session is dead
    res2 = client.get('/admin/dashboard')
    assert res2.status_code == 302
    assert b'/auth/login' in res2.data
