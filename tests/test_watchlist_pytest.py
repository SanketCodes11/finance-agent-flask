import pytest
from unittest.mock import patch
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
def auth_client(client, app):
    with app.app_context():
        user = User(username='test', email='test@test.com')
        user.set_password('Password123')
        db.session.add(user)
        user2 = User(username='test2', email='test2@test.com')
        user2.set_password('Password123')
        db.session.add(user2)
        db.session.commit()
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'})
    return client

def test_unauthenticated_access(client):
    resp = client.post('/api/watchlist', json={'symbol': 'AAPL'})
    assert resp.status_code in [302, 401]

@patch('app.api.finance.get_stock_quote')
def test_add_valid_stock(mock_get_quote, auth_client, app):
    mock_get_quote.return_value = {'name': 'Apple Inc.', 'currency': 'USD', 'exchange': 'NMS'}
    resp = auth_client.post('/api/watchlist', json={'symbol': 'AAPL'})
    assert resp.status_code == 200
    assert resp.json.get('success') is True

    with app.app_context():
        item = Watchlist.query.filter_by(symbol='AAPL').first()
        assert item is not None
        assert item.company_name == 'Apple Inc.'
        assert item.currency == 'USD'
        assert item.exchange == 'NMS'

@patch('app.api.finance.get_stock_quote')
def test_add_invalid_stock(mock_get_quote, auth_client):
    mock_get_quote.side_effect = Exception("Invalid symbol")
    resp = auth_client.post('/api/watchlist', json={'symbol': 'INVALID999'})
    assert resp.status_code == 400
    assert 'error' in resp.json

@patch('app.api.finance.get_stock_quote')
def test_add_duplicate_stock(mock_get_quote, auth_client):
    mock_get_quote.return_value = {'name': 'Microsoft', 'currency': 'USD', 'exchange': 'NMS'}
    auth_client.post('/api/watchlist', json={'symbol': 'MSFT'})
    resp = auth_client.post('/api/watchlist', json={'symbol': 'MSFT'})
    assert resp.status_code == 400
    assert 'error' in resp.json

@patch('app.api.finance.get_stock_quote')
@patch('app.api.finance.get_multiple_stock_quotes')
def test_get_watchlist(mock_multiple, mock_single, auth_client):
    mock_single.return_value = {'name': 'Test', 'currency': 'USD', 'exchange': 'NMS'}
    auth_client.post('/api/watchlist', json={'symbol': 'TSLA'})
    auth_client.post('/api/watchlist', json={'symbol': 'RELIANCE.NS'})
    
    mock_multiple.return_value = {
        'TSLA': {'price': 200.0},
        'RELIANCE.NS': {'price': 3000.0, 'inr_price': 3000.0}
    }
    resp = auth_client.get('/api/watchlist')
    assert resp.status_code == 200
    assert len(resp.json) >= 2

@patch('app.api.finance.get_stock_quote')
def test_remove_stock(mock_get_quote, auth_client, app):
    mock_get_quote.return_value = {'name': 'NVIDIA', 'currency': 'USD', 'exchange': 'NMS'}
    auth_client.post('/api/watchlist', json={'symbol': 'NVDA'})
    resp = auth_client.delete('/api/watchlist', json={'symbol': 'NVDA'})
    assert resp.status_code == 200
    
    with app.app_context():
        item = Watchlist.query.filter_by(symbol='NVDA').first()
        assert item is None

def test_remove_nonexistent_stock(auth_client):
    resp = auth_client.delete('/api/watchlist', json={'symbol': 'UNKNOWN'})
    assert resp.status_code == 404
    
@patch('app.api.finance.get_stock_quote')
@patch('app.api.finance.get_multiple_stock_quotes')
def test_another_user_watchlist(mock_multiple, mock_single, auth_client, app):
    mock_single.return_value = {'name': 'Apple Inc.', 'currency': 'USD', 'exchange': 'NMS'}
    auth_client.post('/api/watchlist', json={'symbol': 'AAPL'})
    
    auth_client.get('/auth/logout')
    auth_client.post('/auth/login', data={'username': 'test2', 'password': 'Password123'})
    
    mock_multiple.return_value = {}
    resp = auth_client.get('/api/watchlist')
    assert len(resp.json) == 0
    
    resp = auth_client.delete('/api/watchlist', json={'symbol': 'AAPL'})
    assert resp.status_code == 404
