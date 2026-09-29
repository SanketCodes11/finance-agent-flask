import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig
from unittest.mock import patch

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

@pytest.fixture
def mock_quote():
    with patch('app.api.finance.get_stock_quote') as mock:
        mock.return_value = {
            'price': 150.0,
            'name': 'Apple Inc.',
            'currency': 'USD',
            'change': 2.5,
            'change_percent': 1.6
        }
        yield mock

from app.models.finance import PortfolioItem, PortfolioTransaction
from app import db

def test_add_transaction_buy(mock_quote, client, auth, app):
    auth.login()
    
    # First BUY
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 10,
        'purchase_price': 100.0,
        'transaction_type': 'BUY'
    })
    assert res.status_code == 200
    
    with app.app_context():
        item = PortfolioItem.query.filter_by(symbol='AAPL').first()
        assert item is not None
        assert item.quantity == 10
        assert item.purchase_price == 100.0
        
        txs = PortfolioTransaction.query.all()
        assert len(txs) == 1
        assert txs[0].transaction_type == 'BUY'

    # Second BUY (Average Cost)
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 10,
        'purchase_price': 200.0,
        'transaction_type': 'BUY'
    })
    assert res.status_code == 200
    
    with app.app_context():
        item = PortfolioItem.query.filter_by(symbol='AAPL').first()
        assert item.quantity == 20
        assert item.purchase_price == 150.0  # (10*100 + 10*200) / 20 = 150
        
        txs = PortfolioTransaction.query.all()
        assert len(txs) == 2

def test_sell_transaction(mock_quote, client, auth, app):
    auth.login()
    
    # Buy 10 AAPL @ 100
    client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 10,
        'purchase_price': 100.0,
        'transaction_type': 'BUY'
    })
    
    # Sell 5 AAPL @ 150 (Partial sell)
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 5,
        'purchase_price': 150.0,
        'transaction_type': 'SELL'
    })
    assert res.status_code == 200
    
    with app.app_context():
        item = PortfolioItem.query.filter_by(symbol='AAPL').first()
        assert item.quantity == 5
        assert item.purchase_price == 100.0  # Cost basis shouldn't change on sell
        
        tx = PortfolioTransaction.query.filter_by(transaction_type='SELL').first()
        assert tx.realized_pl == 250.0  # (150 - 100) * 5
        
    # Oversell (Try to sell 10 when only 5 remaining)
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 10,
        'purchase_price': 150.0,
        'transaction_type': 'SELL'
    })
    assert res.status_code == 400
    assert 'Not enough shares' in res.get_json()['error']
    
    # Sell remaining 5 AAPL (Full sell)
    res = client.post('/api/portfolio', json={
        'symbol': 'AAPL',
        'quantity': 5,
        'purchase_price': 80.0,
        'transaction_type': 'SELL'
    })
    assert res.status_code == 200
    
    with app.app_context():
        item = PortfolioItem.query.filter_by(symbol='AAPL').first()
        assert item is None  # Item should be deleted or 0
        
        # Second SELL transaction
        txs = PortfolioTransaction.query.filter_by(transaction_type='SELL').order_by(PortfolioTransaction.id.desc()).all()
        assert txs[0].realized_pl == -100.0  # (80 - 100) * 5
        
def test_get_transactions(mock_quote, client, auth):
    auth.login()
    client.post('/api/portfolio', json={'symbol': 'AAPL', 'quantity': 10, 'purchase_price': 100.0, 'transaction_type': 'BUY'})
    
    res = client.get('/api/portfolio/transactions')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['symbol'] == 'AAPL'
    assert data[0]['type'] == 'BUY'
    
