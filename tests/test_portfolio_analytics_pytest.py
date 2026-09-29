import pytest
from app.models.finance import PortfolioTransaction
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models.user import User
from config import TestConfig
from datetime import date, timedelta
import pandas as pd
from app.services.portfolio_analytics_service import calculate_portfolio_history, fetch_historical_prices, price_cache, cache_lock

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

@pytest.fixture
def auth(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
    return AuthActions(client)

@pytest.fixture(autouse=True)
def clear_cache():
    # Clear the in-memory cache before every test
    with cache_lock:
        price_cache.clear()

def setup_transactions(user_id):
    today = date.today()
    tx1 = PortfolioTransaction(
        user_id=user_id, symbol='AAPL', transaction_type='BUY', quantity=10, price=100.0,
        transaction_date=today - timedelta(days=5)
    )
    tx2 = PortfolioTransaction(
        user_id=user_id, symbol='AAPL', transaction_type='BUY', quantity=5, price=120.0,
        transaction_date=today - timedelta(days=3)
    )
    tx3 = PortfolioTransaction(
        user_id=user_id, symbol='AAPL', transaction_type='SELL', quantity=5, price=150.0,
        transaction_date=today - timedelta(days=1)
    )
    db.session.add_all([tx1, tx2, tx3])
    db.session.commit()

@patch('app.services.portfolio_analytics_service.yf.download')
def test_fetch_historical_prices(mock_download, app):
    # Mock yfinance dataframe
    start_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d')
    end_date = date.today().strftime('%Y-%m-%d')
    
    dates = pd.date_range(start=start_date, periods=3, freq='D')
    df = pd.DataFrame({'Close': [100.0, 105.0, 110.0]}, index=dates)
    mock_download.return_value = df
    
    with app.app_context():
        prices = fetch_historical_prices('AAPL', start_date, end_date)
        
    assert isinstance(prices, dict)
    # Checks forward fill
    assert start_date in prices
    assert end_date in prices # Forward filled to today

def test_unauthenticated_access(client):
    res = client.get('/api/portfolio/historical')
    assert res.status_code in [401, 302]

@patch('app.services.portfolio_analytics_service.yf.download')
def test_portfolio_history_api(mock_download, client, auth, app):
    auth.login()
    
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        setup_transactions(user.id)
        
    start_date = (date.today() - timedelta(days=10)).strftime('%Y-%m-%d')
    dates = pd.date_range(start=start_date, periods=10, freq='D')
    df = pd.DataFrame({'Close': [100.0] * 10}, index=dates)
    mock_download.return_value = df
    
    res = client.get('/api/portfolio/historical?period=1M')
    assert res.status_code == 200
    data = res.get_json()
    
    assert 'labels' in data
    assert 'market_values' in data
    assert 'invested_capital' in data
    assert 'metrics' in data
    
    metrics = data['metrics']
    assert 'absolute_return' in metrics
    assert 'percentage_return' in metrics
    assert 'peak_value' in metrics
    assert 'max_drawdown' in metrics

@patch('app.services.portfolio_analytics_service.fetch_historical_prices')
def test_engine_chronological_replay(mock_fetch, app):
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        if not user:
            user = User(username='testuser', email='test@example.com')
            user.set_password('Password123')
            db.session.add(user)
            db.session.commit()
            
        today = date.today()
        # Clean DB
        PortfolioTransaction.query.delete()
        
        # Tx1: Buy 10 @ 100 on Day -2
        db.session.add(PortfolioTransaction(user_id=user.id, symbol='AAPL', transaction_type='BUY', quantity=10, price=100.0, transaction_date=today - timedelta(days=2)))
        # Tx2: Sell 5 @ 150 on Day 0
        db.session.add(PortfolioTransaction(user_id=user.id, symbol='AAPL', transaction_type='SELL', quantity=5, price=150.0, transaction_date=today))
        db.session.commit()
        
        # Mock historical prices
        d_minus_2 = (today - timedelta(days=2)).strftime('%Y-%m-%d')
        d_minus_1 = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        d_0 = today.strftime('%Y-%m-%d')
        
        mock_fetch.return_value = {
            d_minus_2: 100.0,
            d_minus_1: 150.0,
            d_0: 150.0
        }
        
        data = calculate_portfolio_history(user.id, period='ALL')
        
        # day -2: Invested = 1000. MV = 10 * 100 = 1000
        # day -1: Invested = 1000. MV = 10 * 150 = 1500
        # day 0: Sell 5. Ratio=0.5. Deduct 500 from invested. Invested = 500. MV = 5 * 150 = 750
        
        assert len(data['labels']) == 3
        assert data['invested_capital'][0] == 1000.0
        assert data['market_values'][0] == 1000.0
        
        assert data['invested_capital'][1] == 1000.0
        assert data['market_values'][1] == 1500.0
        
        assert data['invested_capital'][2] == 500.0
        assert data['market_values'][2] == 750.0
        
        assert data['metrics']['absolute_return'] == 250.0
        assert data['metrics']['percentage_return'] == 50.0 # 250 / 500
        assert data['metrics']['peak_value'] == 1500.0
        
@patch('app.services.portfolio_analytics_service.fetch_historical_prices')
def test_engine_empty_history(mock_fetch, app):
    with app.app_context():
        user = User(username='testuser_empty', email='empty@example.com')
        db.session.add(user)
        db.session.commit()
        
        data = calculate_portfolio_history(user.id, period='1Y')
        assert len(data['labels']) == 0
        assert data['metrics']['absolute_return'] == 0

@patch('app.services.portfolio_analytics_service.yf.download')
def test_invalid_period_fallback(mock_download, client, auth, app):
    auth.login()
    with app.app_context():
        user = User.query.filter_by(username='testuser').first()
        setup_transactions(user.id)
        
    mock_download.return_value = pd.DataFrame() # empty df
    
    # Send INVALID period
    res = client.get('/api/portfolio/historical?period=INVALID_PERIOD')
    assert res.status_code == 200 # Should fallback to 1M and return 200
    
def test_cross_user_isolation(client, auth, app):
    with app.app_context():
        user1 = User.query.filter_by(username='testuser').first()
        setup_transactions(user1.id)
        
        # User 2
        user2 = User(username='otheruser', email='other@example.com')
        user2.set_password('Password123')
        db.session.add(user2)
        db.session.commit()
        
    client.get('/auth/logout')
    
    # Login as User 2
    auth.login('otheruser', 'Password123')
    res = client.get('/api/portfolio/historical')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data['labels']) == 0 # Should not see user1's history
