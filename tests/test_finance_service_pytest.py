import pytest
import time
from unittest.mock import patch, MagicMock
from app import create_app, db
from config import TestConfig
from app.services.finance_service import get_stock_quote, QUOTE_CACHE, QUOTE_CACHE_LOCK, YAHOO_CIRCUIT_BREAKER, YAHOO_CB_LOCK, _check_yahoo_circuit, _trip_yahoo_circuit

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(autouse=True)
def clear_caches():
    with QUOTE_CACHE_LOCK:
        QUOTE_CACHE.clear()
    with YAHOO_CB_LOCK:
        YAHOO_CIRCUIT_BREAKER['is_open'] = False
        YAHOO_CIRCUIT_BREAKER['opened_at'] = 0
    yield

def test_twelvedata_success(app):
    app.config['TWELVE_DATA_API_KEY'] = 'test-key'
    
    with patch('app.services.finance_service.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'status': 'ok',
            'symbol': 'AAPL',
            'close': '150.0',
            'previous_close': '145.0',
            'change': '5.0',
            'percent_change': '3.45',
            'currency': 'USD',
            'exchange': 'NASDAQ'
        }
        mock_get.return_value = mock_resp
        
        with app.app_context():
            result = get_stock_quote('AAPL')
            
            assert result['symbol'] == 'AAPL'
            assert result['price'] == 150.0
            assert result['provider'] == 'Twelve Data'
            assert mock_get.call_count == 2  # Once for quote, once for USD/INR forex
            
            # Check cache
            with QUOTE_CACHE_LOCK:
                assert 'AAPL' in QUOTE_CACHE

def test_twelvedata_missing_key_fallback_yahoo(app):
    app.config['TWELVE_DATA_API_KEY'] = ''
    
    with patch('app.services.finance_service._fetch_yahoo_quote') as mock_yahoo:
        mock_yahoo.return_value = {
            'symbol': 'AAPL',
            'price': 160.0,
            'provider': 'Yahoo Finance'
        }
        
        with app.app_context():
            result = get_stock_quote('AAPL')
            
            assert result['price'] == 160.0
            assert result['provider'] == 'Yahoo Finance'
            assert mock_yahoo.call_count == 1

def test_twelvedata_rate_limit_fallback_yahoo(app):
    app.config['TWELVE_DATA_API_KEY'] = 'test-key'
    
    with patch('app.services.finance_service.requests.get') as mock_get, \
         patch('app.services.finance_service._fetch_yahoo_quote') as mock_yahoo:
         
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'status': 'error', 'code': 429, 'message': 'Rate limited'}
        mock_get.return_value = mock_resp
        
        mock_yahoo.return_value = {'symbol': 'AAPL', 'price': 165.0, 'provider': 'Yahoo Finance'}
        
        with app.app_context():
            result = get_stock_quote('AAPL')
            
            assert result['price'] == 165.0
            assert result['provider'] == 'Yahoo Finance'
            assert mock_get.call_count == 1
            assert mock_yahoo.call_count == 1

def test_yahoo_circuit_breaker(app):
    app.config['TWELVE_DATA_API_KEY'] = ''
    
    with patch('app.services.finance_service.yf.Ticker') as mock_ticker:
        mock_ticker.side_effect = Exception("429 Too Many Requests")
        
        with app.app_context():
            with pytest.raises(ValueError, match="Market data currently unavailable"):
                get_stock_quote('AAPL')
                
            # Circuit should be open
            assert not _check_yahoo_circuit()
            
            # Second call should fail immediately without calling yfinance
            mock_ticker.reset_mock()
            with pytest.raises(ValueError, match="Market data currently unavailable"):
                get_stock_quote('AAPL')
                
            assert mock_ticker.call_count == 0

def test_caching_prevents_duplicate_calls(app):
    app.config['TWELVE_DATA_API_KEY'] = 'test-key'
    
    with patch('app.services.finance_service.requests.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            'status': 'ok',
            'symbol': 'AAPL',
            'close': '150.0'
        }
        mock_get.return_value = mock_resp
        
        with app.app_context():
            res1 = get_stock_quote('AAPL')
            res2 = get_stock_quote('AAPL')
            
            assert res1['price'] == 150.0
            assert res2['price'] == 150.0
            # Only 2 HTTP calls should be made because of the cache (Quote + Forex)
            assert mock_get.call_count == 2
