import pytest
from app import create_app, db
from app.models.user import User
from app.models.finance import FinancialGoal, SearchHistory, LoginHistory, UserSettings
from config import TestConfig
from datetime import date, datetime, timedelta, timezone
import json

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

class AuthActions:
    def __init__(self, client):
        self.client = client
    def login(self, username='testuser', password='Password123'):
        return self.client.post('/auth/login', data={'username': username, 'password': password})
    def logout(self):
        return self.client.get('/auth/logout')

@pytest.fixture
def auth(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
    return AuthActions(client)

# ================================
# MODULE A: GOALS TESTS
# ================================

def test_goals_unauthorized(client):
    res = client.get('/api/workspace/goals')
    assert res.status_code in [401, 302]

def test_create_and_get_goal(client, auth, app):
    auth.login()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    
    # Create goal
    res = client.post('/api/workspace/goals', json={
        'name': 'Buy House',
        'target_amount': 100000,
        'current_savings': 20000,
        'monthly_contribution': 5000,
        'target_date': future_date
    }, headers={'X-CSRFToken': 'dummy'})
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    goal_id = data['goal_id']
    
    # Get goals
    res = client.get('/api/workspace/goals')
    data = res.get_json()
    assert len(data['goals']) == 1
    goal = data['goals'][0]
    
    assert goal['name'] == 'Buy House'
    assert goal['target_amount'] == 100000.0
    assert goal['remaining_amount'] == 80000.0
    assert goal['progress_pct'] == 20.0
    assert goal['months_left'] == 12
    # 80000 / 12 = 6666.67 required
    assert goal['required_monthly'] == 6666.67
    # 20000 + (5000 * 12) = 80000 projected
    assert goal['projected_amount'] == 80000.0
    assert goal['is_achieved'] is False

def test_goal_invalid_date(client, auth, app):
    auth.login()
    past_date = (date.today() - timedelta(days=365)).isoformat()
    
    res = client.post('/api/workspace/goals', json={
        'name': 'Past Goal',
        'target_amount': 1000,
        'target_date': past_date
    }, headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 400
    assert 'future' in res.get_json()['error']

def test_goal_already_achieved(client, auth, app):
    auth.login()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    
    client.post('/api/workspace/goals', json={
        'name': 'Achieved',
        'target_amount': 5000,
        'current_savings': 5500,
        'target_date': future_date
    }, headers={'X-CSRFToken': 'dummy'})
    
    res = client.get('/api/workspace/goals')
    goal = res.get_json()['goals'][0]
    
    assert goal['remaining_amount'] == 0.0
    assert goal['progress_pct'] == 100.0
    assert goal['is_achieved'] is True
    assert goal['required_monthly'] == 0.0

def test_goal_update_and_delete(client, auth, app):
    auth.login()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    
    res = client.post('/api/workspace/goals', json={
        'name': 'Temp',
        'target_amount': 1000,
        'target_date': future_date
    }, headers={'X-CSRFToken': 'dummy'})
    goal_id = res.get_json()['goal_id']
    
    # Update
    res = client.put(f'/api/workspace/goals/{goal_id}', json={
        'name': 'Updated',
        'target_amount': 2000
    }, headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 200
    
    res = client.get('/api/workspace/goals')
    goal = res.get_json()['goals'][0]
    assert goal['name'] == 'Updated'
    assert goal['target_amount'] == 2000.0
    
    # Delete
    res = client.delete(f'/api/workspace/goals/{goal_id}', headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 200
    
    res = client.get('/api/workspace/goals')
    assert len(res.get_json()['goals']) == 0

def test_goal_cross_user_isolation(client, auth, app):
    auth.login()
    future_date = (date.today() + timedelta(days=365)).isoformat()
    client.post('/api/workspace/goals', json={
        'name': 'User1 Goal',
        'target_amount': 1000,
        'target_date': future_date
    }, headers={'X-CSRFToken': 'dummy'})
    
    auth.logout()
    
    with app.app_context():
        user2 = User(username='other', email='other@example.com')
        user2.set_password('pass')
        db.session.add(user2)
        db.session.commit()
        
    auth.login('other', 'pass')
    res = client.get('/api/workspace/goals')
    assert len(res.get_json()['goals']) == 0

# ================================
# MODULE B: WORKSPACE TESTS
# ================================

def test_search_history_api(client, auth, app):
    auth.login()
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        db.session.add(SearchHistory(user_id=user.id, symbol='AAPL'))
        db.session.add(SearchHistory(user_id=user.id, symbol='MSFT'))
        db.session.commit()
        
    res = client.get('/api/workspace/history/search')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['history']) == 2
    
    # Delete history
    res = client.delete('/api/workspace/history/search', headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 200
    
    res = client.get('/api/workspace/history/search')
    assert len(res.get_json()['history']) == 0

def test_login_history_api(client, auth, app):
    auth.login()
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        db.session.add(LoginHistory(user_id=user.id, ip_address='127.0.0.1', user_agent='TestAgent'))
        db.session.commit()
        
    res = client.get('/api/workspace/history/login')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['history']) >= 1
    assert data['history'][0]['ip_address'] == '127.0.0.1'

def test_user_settings(client, auth, app):
    auth.login()
    
    # Get defaults
    res = client.get('/api/workspace/settings')
    assert res.get_json()['preferred_currency'] == 'USD'
    
    # Update
    res = client.put('/api/workspace/settings', json={
        'preferred_currency': 'INR',
        'theme': 'dark'
    }, headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 200
    
    # Verify
    res = client.get('/api/workspace/settings')
    data = res.get_json()
    assert data['preferred_currency'] == 'INR'
    assert data['theme'] == 'dark'

def test_change_password(client, auth, app):
    auth.login()
    
    # Wrong current password
    res = client.post('/api/workspace/security/password', json={
        'current_password': 'WrongPassword',
        'new_password': 'NewPassword123'
    }, headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 401
    
    # Correct current password
    res = client.post('/api/workspace/security/password', json={
        'current_password': 'Password123',
        'new_password': 'NewPassword123'
    }, headers={'X-CSRFToken': 'dummy'})
    assert res.status_code == 200
    
    # Try logging in with old and new
    auth.logout()
    res = auth.login('testuser', 'Password123')
    assert 'Invalid username or password' in res.get_data(as_text=True) # Assuming this is flash message, but we just check if it doesn't redirect to next usually
    
    res = auth.login('testuser', 'NewPassword123')
    assert res.status_code == 302 # Success redirect
