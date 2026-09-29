import pytest
from app import create_app, db
from app.models.user import User
from app.models.finance import Watchlist
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
        
        normal = User(username='target_user', email='target@test.com', is_admin=False, is_active=True)
        normal.set_password('pass123')
        
        db.session.add_all([admin, normal])
        db.session.commit()
        
        w = Watchlist(user_id=normal.id, symbol='AAPL')
        db.session.add(w)
        db.session.commit()
        
        return normal.id

def login(client, username, password, is_admin=False):
    endpoint = '/admin/login' if is_admin else '/auth/login'
    return client.post(endpoint, data={'username': username, 'password': password}, follow_redirects=True)

def test_user_detail_access_denied(client, setup_data):
    user_id = setup_data
    # Unauthenticated
    res = client.get(f'/admin/users/{user_id}')
    assert res.status_code == 403
    
    # Normal user
    login(client, 'target_user', 'pass123')
    res = client.get(f'/admin/users/{user_id}')
    assert res.status_code == 403

def test_user_detail_success(client, setup_data):
    user_id = setup_data
    login(client, 'admin', 'pass123', is_admin=True)
    
    res = client.get(f'/admin/users/{user_id}')
    assert res.status_code == 200
    assert b'target_user' in res.data
    assert b'AAPL' in res.data # Should show watchlist item
    assert b'User 360' in res.data
