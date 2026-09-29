import pytest
from app.models.finance import VirtualAccount, VirtualPosition, VirtualOrder
from unittest.mock import patch
from app import create_app, db
from app.models.user import User
from config import TestConfig
from decimal import Decimal

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
    res = client.get('/api/paper-trade/account')
    assert res.status_code in [302, 401]

def test_account_creation_and_balance(client, auth):
    auth.login()
    # First access creates the account
    res = client.get('/api/paper-trade/account')
    assert res.status_code == 200
    data = res.get_json()
    assert data['initial_balance'] == 1000000.0
    assert data['current_cash'] == 1000000.0
    assert data['portfolio_value'] == 0.0
    assert len(data['holdings']) == 0

@patch('app.api.paper_trading.get_stock_quote')
def test_successful_buy_and_cash_deduction(mock_quote, client, auth):
    auth.login()
    
    # Mock stock price to $150.00
    mock_quote.return_value = {'price': 150.00, 'symbol': 'AAPL'}
    
    # Initialize account
    auth.login()
    client.get('/api/paper-trade/account')
    
    # Execute BUY
    res = client.post('/api/paper-trade/order', json={
        'symbol': 'AAPL',
        'order_type': 'BUY',
        'quantity': 10
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['execution_price'] == 150.0
    assert data['transaction_value'] == 1500.0
    
    # Verify account cash deduction and position
    res = client.get('/api/paper-trade/account')
    account = res.get_json()
    assert account['current_cash'] == 998500.0  # 1000000 - 1500
    assert len(account['holdings']) == 1
    assert account['holdings'][0]['symbol'] == 'AAPL'
    assert account['holdings'][0]['quantity'] == 10.0
    assert account['holdings'][0]['avg_price'] == 150.0

@patch('app.api.paper_trading.get_stock_quote')
def test_multiple_buy_orders_weighted_avg(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    # Buy 10 @ 100
    mock_quote.return_value = {'price': 100.00}
    client.post('/api/paper-trade/order', json={'symbol': 'TSLA', 'order_type': 'BUY', 'quantity': 10})
    
    # Buy 10 @ 200
    mock_quote.return_value = {'price': 200.00}
    client.post('/api/paper-trade/order', json={'symbol': 'TSLA', 'order_type': 'BUY', 'quantity': 10})
    
    res = client.get('/api/paper-trade/account')
    holdings = res.get_json()['holdings']
    tsla = next(h for h in holdings if h['symbol'] == 'TSLA')
    
    assert tsla['quantity'] == 20.0
    assert tsla['avg_price'] == 150.0 # (1000 + 2000) / 20 = 150

@patch('app.api.paper_trading.get_stock_quote')
def test_insufficient_cash(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    mock_quote.return_value = {'price': 1000.00}
    
    # Attempt to buy more than $1M worth (1001 shares = $1,001,000)
    res = client.post('/api/paper-trade/order', json={'symbol': 'BRK.A', 'order_type': 'BUY', 'quantity': 1001})
    assert res.status_code == 400
    assert 'Insufficient virtual cash' in res.get_json()['error']

@patch('app.api.paper_trading.get_stock_quote')
def test_successful_sell_partial_close(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    mock_quote.return_value = {'price': 100.00}
    client.post('/api/paper-trade/order', json={'symbol': 'MSFT', 'order_type': 'BUY', 'quantity': 10})
    
    # Sell 5 shares @ 150
    mock_quote.return_value = {'price': 150.00}
    res = client.post('/api/paper-trade/order', json={'symbol': 'MSFT', 'order_type': 'SELL', 'quantity': 5})
    assert res.status_code == 200
    
    account = client.get('/api/paper-trade/account').get_json()
    assert account['current_cash'] == 999750.0 # 1000000 - 1000 + 750
    msft = next(h for h in account['holdings'] if h['symbol'] == 'MSFT')
    assert msft['quantity'] == 5.0

@patch('app.api.paper_trading.get_stock_quote')
def test_full_position_close(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    mock_quote.return_value = {'price': 10.00}
    client.post('/api/paper-trade/order', json={'symbol': 'PENNY', 'order_type': 'BUY', 'quantity': 100})
    
    # Sell all 100 shares
    res = client.post('/api/paper-trade/order', json={'symbol': 'PENNY', 'order_type': 'SELL', 'quantity': 100})
    assert res.status_code == 200
    
    account = client.get('/api/paper-trade/account').get_json()
    assert len([h for h in account['holdings'] if h['symbol'] == 'PENNY']) == 0

@patch('app.api.paper_trading.get_stock_quote')
def test_insufficient_shares_to_sell(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    mock_quote.return_value = {'price': 50.00}
    client.post('/api/paper-trade/order', json={'symbol': 'AMD', 'order_type': 'BUY', 'quantity': 10})
    
    # Try selling 15 shares
    res = client.post('/api/paper-trade/order', json={'symbol': 'AMD', 'order_type': 'SELL', 'quantity': 15})
    assert res.status_code == 400
    assert 'Insufficient shares to sell' in res.get_json()['error']

def test_invalid_quantity(client, auth):
    auth.login()
    res = client.post('/api/paper-trade/order', json={'symbol': 'AMD', 'order_type': 'BUY', 'quantity': -5})
    assert res.status_code == 400

@patch('app.api.paper_trading.get_stock_quote')
def test_failed_market_price_retrieval(mock_quote, client, auth):
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    
    mock_quote.return_value = None # API failure
    res = client.post('/api/paper-trade/order', json={'symbol': 'FAKE', 'order_type': 'BUY', 'quantity': 10})
    assert res.status_code == 400
    assert 'Failed to retrieve live market data' in res.get_json()['error']

def test_cross_user_isolation(client, app, auth):
    # Setup testuser1
    auth.login()
    auth.login()
    client.get('/api/paper-trade/account')
    with app.app_context():
        # Modify DB directly to give testuser 1500000 cash for easy check
        user1 = db.session.execute(db.text("SELECT id FROM user WHERE username='testuser'")).scalar()
        db.session.execute(db.text(f"UPDATE virtual_account SET current_cash=1500000 WHERE user_id={user1}"))
        db.session.commit()
    
    auth.logout()
    
    # Setup User2
    with app.app_context():
        user2 = User(username='otheruser', email='other@example.com')
        user2.set_password('Password123')
        db.session.add(user2)
        db.session.commit()
        
    auth.login('otheruser', 'Password123')
    res = client.get('/api/paper-trade/account')
    assert res.get_json()['current_cash'] == 1000000.0 # Initial default, isolated from testuser

def test_wallet_deposit(client, auth):
    # Load account to initialize it
    auth.login()
    client.get('/api/paper-trade/account')
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': 50000
    })
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['new_balance'] == 1050000.0
    
    # Check history
    res = client.get('/api/paper-trade/wallet/history')
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['type'] == 'DEPOSIT'
    assert data[0]['amount'] == 50000

def test_wallet_withdraw_success(client, auth):
    auth.login()
    client.get('/api/paper-trade/account')
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'WITHDRAW',
        'amount': 100000
    })
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['new_balance'] == 900000.0

def test_wallet_withdraw_insufficient_funds(client, auth):
    auth.login()
    client.get('/api/paper-trade/account')
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'WITHDRAW',
        'amount': 2000000 # More than initial 1,000,000
    })
    
    assert res.status_code == 400
    assert 'Insufficient available cash' in res.get_json()['error']

def test_wallet_invalid_amount(client, auth):
    auth.login()
    client.get('/api/paper-trade/account')
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': -500
    })
    assert res.status_code == 400
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': 'invalid'
    })
    assert res.status_code == 400
