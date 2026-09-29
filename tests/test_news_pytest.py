import pytest
from unittest.mock import patch
from app import create_app, db
from app.models.user import User
from app.services.finance_service import get_financial_news, NewsAPIError, NewsNotConfiguredError

from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    app.config.update({
        "NEWS_API_KEY": "dummy_key"
    })
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

def test_missing_api_key(client, app):
    print("\n--- Testing Missing API Key ---")
    app.config['NEWS_API_KEY'] = 'your-newsapi-key-here'
    with app.app_context():
        with pytest.raises(NewsNotConfiguredError):
            get_financial_news('Apple')

def test_missing_api_key_route(auth_client, app):
    app.config['NEWS_API_KEY'] = None
    resp = auth_client.get('/api/news?q=Apple')
    assert resp.status_code == 503
    assert resp.json.get('not_configured') is True
    print("[SUCCESS] Missing API key handled safely.")

@patch('app.services.finance_service.requests.get')
def test_valid_news_search(mock_get, auth_client, app):
    print("\n--- Testing Valid News Search ---")
    # clear cache
    import app.services.finance_service as fs
    fs.NEWS_CACHE.clear()

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        'articles': [
            {
                'title': 'Test Article',
                'description': 'Test Description',
                'url': 'http://test.com',
                'source': {'name': 'Test Source'},
                'publishedAt': '2023-01-01T00:00:00Z',
                'urlToImage': 'http://test.com/img.jpg'
            },
            {
                'title': 'Missing Image',
                'description': None,
                'url': 'http://test.com/2',
                'source': {'name': 'Test Source 2'},
                'publishedAt': '2023-01-01T00:00:00Z',
                'urlToImage': None
            }
        ]
    }
    
    resp = auth_client.get('/api/news?q=Reliance')
    assert resp.status_code == 200
    assert len(resp.json['articles']) == 2
    assert resp.json['articles'][0]['title'] == 'Test Article'
    assert resp.json['articles'][1]['description'] is None
    print("[SUCCESS] Fetched valid news with missing image fallback.")

@patch('app.services.finance_service.requests.get')
def test_no_results(mock_get, auth_client):
    print("\n--- Testing No Results ---")
    import app.services.finance_service as fs
    fs.NEWS_CACHE.clear()

    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {'articles': []}
    
    resp = auth_client.get('/api/news?q=XYZNonExistent')
    assert resp.status_code == 200
    assert len(resp.json['articles']) == 0
    print("[SUCCESS] No results handled correctly.")

@patch('app.services.finance_service.requests.get')
def test_rate_limit(mock_get, auth_client):
    print("\n--- Testing Rate Limit ---")
    import app.services.finance_service as fs
    fs.NEWS_CACHE.clear()

    mock_get.return_value.status_code = 429
    
    resp = auth_client.get('/api/news?q=finance')
    assert resp.status_code == 502
    assert 'rate limit' in resp.json['error'].lower()
    print("[SUCCESS] Rate limit handled safely.")

@patch('app.services.finance_service.requests.get')
def test_invalid_api_key_401(mock_get, auth_client):
    print("\n--- Testing Invalid API Key ---")
    import app.services.finance_service as fs
    fs.NEWS_CACHE.clear()

    mock_get.return_value.status_code = 401
    
    resp = auth_client.get('/api/news?q=finance')
    assert resp.status_code == 502
    assert 'invalid' in resp.json['error'].lower()
    print("[SUCCESS] Invalid API key handled safely.")
