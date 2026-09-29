import pytest
from app.models.finance import PortfolioItem
from datetime import date
from unittest.mock import patch
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

def test_unauthenticated_access(client):
    """Test that unauthenticated users cannot access portfolio endpoints."""
    res = client.get('/portfolio')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']
    
    res = client.get('/api/portfolio')
    assert res.status_code == 401

def test_get_empty_portfolio(client, auth):
    """Test getting portfolio when empty."""
    auth.login()
    res = client.get('/api/portfolio')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 0

@patch('app.api.finance.get_stock_quote')
def test_add_portfolio_item(mock_quote, client, auth, app):
    """Test adding a new portfolio item."""
    auth.login()
    mock_quote.return_value = {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'currency': 'USD',
        'price': 150.0
    }
    
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 10,
        'purchase_price': 140.0,
        'purchase_date': '2023-01-01'
    })
    
    assert res.status_code == 200
    assert res.get_json()['success'] is True
    
    with app.app_context():
        item = PortfolioItem.query.filter_by(symbol='AAPL').first()
        assert item is not None
        assert item.quantity == 10
        assert item.purchase_price == 140.0
        assert item.purchase_date == date(2023, 1, 1)

@patch('app.api.finance.get_stock_quote')
def test_add_portfolio_item_invalid_data(mock_quote, client, auth):
    """Test adding with invalid data (negative quantity/price)."""
    auth.login()
    
    # Negative quantity
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': -5,
        'purchase_price': 140.0
    })
    assert res.status_code == 400
    assert 'Quantity must be > 0' in res.get_json()['error']
    
    # Missing required fields
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL'
    })
    assert res.status_code == 400

@patch('app.api.finance.get_stock_quote')
@patch('app.api.finance.get_multiple_stock_quotes')
def test_get_portfolio_calculations(mock_quotes, mock_quote, client, auth, app):
    """Test that total cost, current value, and unrealized P/L are calculated correctly."""
    auth.login()
    
    # Add item
    mock_quote.return_value = {'symbol': 'MSFT', 'name': 'Microsoft', 'currency': 'USD'}
    client.post('/api/portfolio', json={
        'symbol': 'MSFT',
        'quantity': 5,
        'purchase_price': 300.0
    })
    
    # Mock current price
    mock_quotes.return_value = {
        'MSFT': {'symbol': 'MSFT', 'name': 'Microsoft', 'currency': 'USD', 'price': 350.0}
    }
    
    res = client.get('/api/portfolio')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    
    item = data[0]
    assert item['total_cost'] == 1500.0  # 5 * 300
    assert item['current_value'] == 1750.0  # 5 * 350
    assert item['unrealized_pl'] == 250.0  # 1750 - 1500
    assert item['unrealized_pl_pct'] == (250.0 / 1500.0) * 100

def test_update_portfolio_item(client, auth, app):
    """Test editing a portfolio holding."""
    auth.login()
    
    # Create item directly in DB
    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email='test@example.com').first()
        item = PortfolioItem(user_id=user.id, symbol='TSLA', quantity=2, purchase_price=200.0)
        from app import db
        db.session.add(item)
        db.session.commit()
        item_id = item.id
        
    res = client.put(f'/api/portfolio/{item_id}', json={
        'quantity': 4,
        'purchase_price': 210.0
    })
    
    assert res.status_code == 200
    
    with app.app_context():
        updated = PortfolioItem.query.get(item_id)
        assert updated.quantity == 4
        assert updated.purchase_price == 210.0

def test_delete_portfolio_item(client, auth, app):
    """Test removing a portfolio holding."""
    auth.login()
    
    with app.app_context():
        from app.models.user import User
        user = User.query.filter_by(email='test@example.com').first()
        item = PortfolioItem(user_id=user.id, symbol='NVDA', quantity=10, purchase_price=100.0)
        from app import db
        db.session.add(item)
        db.session.commit()
        item_id = item.id
        
    res = client.delete(f'/api/portfolio/{item_id}')
    assert res.status_code == 200
    
    with app.app_context():
        deleted = PortfolioItem.query.get(item_id)
        assert deleted is None

def test_cross_user_portfolio_access(client, auth, app):
    """Test that users cannot edit or delete other users' portfolio items."""
    with app.app_context():
        from app.models.user import User
        from app import db
        # Create second user
        u2 = User(username='testuser2', email='test2@example.com')
        u2.set_password('password123')
        db.session.add(u2)
        db.session.commit()
        
        # Add item for User 2
        item = PortfolioItem(user_id=u2.id, symbol='GOOGL', quantity=10, purchase_price=100.0)
        db.session.add(item)
        db.session.commit()
        item_id = item.id
        
    # Log in as User 1
    auth.login()
    
    # Attempt to update User 2's item
    res = client.put(f'/api/portfolio/{item_id}', json={'quantity': 50})
    assert res.status_code == 404
    
    # Attempt to delete User 2's item
    res = client.delete(f'/api/portfolio/{item_id}')
    assert res.status_code == 404
    
    # Verify item is untouched
    with app.app_context():
        untouched = PortfolioItem.query.get(item_id)
        assert untouched is not None
        assert untouched.quantity == 10
