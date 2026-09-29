import pytest
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

@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='test', email='test@test.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'})
    return client

@patch('app.api.finance.search_stocks')
def test_autocomplete(mock_search_stocks, auth_client):
    mock_search_stocks.return_value = [{'symbol': 'AAPL', 'name': 'Apple Inc.'}]
    
    queries = ["TCS", "Infosys", "Reliance", "Apple", "Microsoft", "Tesla"]
    for q in queries:
        resp = auth_client.get(f"/api/stock/autocomplete?q={q}")
        assert resp.status_code == 200
        data = resp.json
        assert len(data) > 0

def test_empty_autocomplete(auth_client):
    resp = auth_client.get("/api/stock/autocomplete?q=")
    assert resp.status_code == 200
    assert len(resp.json) == 0

@patch('app.api.finance.get_stock_quote')
def test_indian_symbols(mock_get_quote, auth_client):
    mock_get_quote.return_value = {'price': 1000.0, 'currency': 'INR', 'exchange': 'NSE'}
    
    indian_symbols = ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFCBANK.NS", "SBIN.NS"]
    for sym in indian_symbols:
        resp = auth_client.get(f"/api/stock/search?q={sym}")
        assert resp.status_code == 200
        assert resp.json['currency'] == 'INR'

@patch('app.api.finance.get_stock_quote')
def test_international_symbols(mock_get_quote, auth_client):
    # Mocking external call to prevent yfinance failures like "NVDA possibly delisted"
    mock_get_quote.return_value = {'price': 150.0, 'currency': 'USD', 'inr_price': 12500.0}
    
    intl_symbols = ["AAPL", "MSFT", "TSLA", "NVDA"]
    for sym in intl_symbols:
        resp = auth_client.get(f"/api/stock/search?q={sym}")
        assert resp.status_code == 200
        assert resp.json['currency'] == 'USD'

@patch('app.api.finance.get_stock_quote')
def test_invalid_ticker(mock_get_quote, auth_client):
    mock_get_quote.side_effect = Exception("Invalid ticker")
    resp = auth_client.get("/api/stock/search?q=INVALID_TICKER_999")
    assert resp.status_code == 404
    assert 'error' in resp.json

@patch('app.api.finance.get_stock_quote')
def test_rate_limit_yahoo(mock_get_quote, auth_client):
    mock_get_quote.side_effect = ValueError("Market data currently unavailable (Yahoo rate limited).")
    resp = auth_client.get("/api/stock/search?q=RELIANCE.NS")
    assert resp.status_code == 404
    assert 'Market data currently unavailable' in resp.json['error']

def test_stock_detail_view_loads(auth_client):
    resp = auth_client.get("/stock/RELIANCE.NS")
    assert resp.status_code == 200
    assert b"RELIANCE.NS" in resp.data
    assert b"AI Analyst Insight" in resp.data
