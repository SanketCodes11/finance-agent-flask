import pytest
from app import create_app, db
from app.models.user import User, AdminAuditLog
from app.models.finance import LoginHistory, SearchHistory
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
def setup_data(app):
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', is_admin=True, is_active=True)
        admin.set_password('pass123')
        
        normal = User(username='normal', email='normal@test.com', is_admin=False, is_active=True)
        normal.set_password('pass123')
        
        db.session.add_all([admin, normal])
        db.session.commit()
        
        # Add histories
        lh = LoginHistory(user_id=normal.id, ip_address='192.168.1.1', user_agent='TestBrowser')
        sh = SearchHistory(user_id=normal.id, symbol='AAPL')
        al = AdminAuditLog(admin_id=admin.id, action='test_action', details='{}')
        
        db.session.add_all([lh, sh, al])
        db.session.commit()

def login(client, username, password, is_admin=False):
    endpoint = '/admin/login' if is_admin else '/auth/login'
    return client.post(endpoint, data={'username': username, 'password': password}, follow_redirects=True)

def test_activity_unauthorized(client, setup_data):
    login(client, 'normal', 'pass123')
    res = client.get('/admin/activity')
    assert res.status_code == 403

def test_activity_authorized(client, setup_data):
    login(client, 'admin', 'pass123', is_admin=True)
    res = client.get('/admin/activity')
    assert res.status_code == 200
    # Check if unified events are present
    assert b'AAPL' in res.data
    assert b'TestBrowser' in res.data
    assert b'test_action' in res.data
    assert b'normal' in res.data

def test_activity_search_filter(client, setup_data):
    login(client, 'admin', 'pass123', is_admin=True)
    res = client.get('/admin/activity?event=login')
    assert res.status_code == 200
    assert b'TestBrowser' in res.data
    assert b'test_action' not in res.data # Admin log filtered out
    assert b'AAPL' not in res.data # Search history filtered out
