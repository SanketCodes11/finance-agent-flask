import pytest
from app import create_app, db
from app.models.user import User, AdminAuditLog
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

def login(client, username, password, is_admin=False):
    endpoint = '/admin/login' if is_admin else '/auth/login'
    return client.post(endpoint, data={'username': username, 'password': password}, follow_redirects=True)

def test_dashboard_access_denied_for_normal_user(client, setup_users):
    login(client, 'normal', 'pass123')
    res = client.get('/admin/dashboard')
    assert res.status_code == 403

def test_dashboard_access_allowed_for_admin(client, setup_users):
    login(client, 'admin', 'pass123', is_admin=True)
    res = client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b'Super Admin Dashboard' in res.data
    assert b'normal@test.com' not in res.data # Just checking dashboard doesn't list all users here directly

def test_user_management_view(client, setup_users):
    login(client, 'admin', 'pass123', is_admin=True)
    res = client.get('/admin/users')
    assert res.status_code == 200
    assert b'normal@test.com' in res.data
    assert b'admin@test.com' in res.data

def test_toggle_active_normal_user(client, app, setup_users):
    login(client, 'admin', 'pass123', is_admin=True)
    with app.app_context():
        normal = User.query.filter_by(username='normal').first()
        normal_id = normal.id
        
    res = client.post(f'/admin/users/{normal_id}/toggle_active', follow_redirects=True)
    assert res.status_code == 200
    assert b'has been deactivated' in res.data
    
    with app.app_context():
        normal = User.query.get(normal_id)
        assert not normal.is_active
        # Check audit log
        log = AdminAuditLog.query.filter_by(action='deactivated_user').first()
        assert log is not None
        assert str(normal_id) == log.record_id

def test_last_admin_protection_deactivate(client, app, setup_users):
    login(client, 'admin', 'pass123', is_admin=True)
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        admin_id = admin.id
        
    res = client.post(f'/admin/users/{admin_id}/toggle_active', follow_redirects=True)
    assert res.status_code == 200
    assert b'Action Blocked: You cannot deactivate the last active super admin' in res.data
    
    with app.app_context():
        admin = User.query.get(admin_id)
        assert admin.is_active  # Still active

def test_last_admin_protection_demote(client, app, setup_users):
    login(client, 'admin', 'pass123', is_admin=True)
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        admin_id = admin.id
        
    res = client.post(f'/admin/users/{admin_id}/toggle_admin', follow_redirects=True)
    assert res.status_code == 200
    assert b'Action Blocked: You cannot demote the last active super admin' in res.data
    
    with app.app_context():
        admin = User.query.get(admin_id)
        assert admin.is_admin  # Still admin
