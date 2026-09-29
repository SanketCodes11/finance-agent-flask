import pytest
from app.models.user import User
from app.models.finance import Watchlist
from app import db
from tests.test_auth import app, client

def login(client, username, password):
    return client.post('/auth/login', data=dict(
        username=username,
        password=password
    ), follow_redirects=True)

def test_search_unauthorized(client):
    response = client.get('/api/stock/search?q=AAPL')
    assert response.status_code == 401

def test_search_authorized_no_symbol(client, app):
    with app.app_context():
        user = User(username='testuser2', email='test2@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
    login(client, 'testuser2', 'password123')
    response = client.get('/api/stock/search')
    assert response.status_code == 400
    assert b'Symbol is required' in response.data

# Note: We won't test external API calls directly to avoid rate limits/network issues in unit tests,
# but we can mock them if necessary. For now, testing the authorization layer.
