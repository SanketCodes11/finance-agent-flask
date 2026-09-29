import pytest
from unittest.mock import patch
from app import create_app, db
from app.models.user import User
from app.services.ai_service import fetch_agent_insight

from config import TestConfig

@pytest.fixture
def app():
    # Pass TestConfig to create_app before db.init_app is called
    app = create_app(TestConfig)
    app.config.update({
        "GEMINI_API_KEY": "dummy_key",
        "NEWS_API_KEY": "dummy_news_key"
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
    print("\n--- Testing Missing Gemini API Key ---")
    app.config['GEMINI_API_KEY'] = 'your-gemini-api-key-here' # Unconfigured fallback state
    import os
    os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
    with app.app_context():
        with pytest.raises(Exception) as exc:
            fetch_agent_insight("Hello")
        assert "not configured" in str(exc.value).lower()
        print("[SUCCESS] Missing API key handled safely.")

@patch('app.services.ai_service.genai.Client')
def test_valid_agent_query(mock_client_cls, auth_client, app):
    print("\n--- Testing Valid Agent Query ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    mock_chat.send_message.return_value.text = "This is a mock response from Gemini analyzing AAPL."
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    resp = auth_client.post('/api/agent/ask', json={'query': 'What about AAPL?'})
    assert resp.status_code == 200
    assert "mock response" in resp.json['response']
    print("[SUCCESS] Valid query processed successfully.")

@patch('app.services.ai_service.genai.Client')
def test_history_context(mock_client_cls, auth_client, app):
    print("\n--- Testing Chat History Context ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    mock_chat.send_message.return_value.text = "AAPL is Apple."
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    history = [
        {"role": "user", "text": "What about AAPL?"},
        {"role": "model", "text": "Apple is doing well."}
    ]
    resp = auth_client.post('/api/agent/ask', json={'query': 'Compare it with MSFT', 'history': history})
    assert resp.status_code == 200
    assert "AAPL is Apple" in resp.json['response']
    
    # Check that create was called with history
    mock_client_cls.return_value.chats.create.assert_called_once()
    kwargs = mock_client_cls.return_value.chats.create.call_args.kwargs
    assert 'history' in kwargs
    assert len(kwargs['history']) == 2
    print("[SUCCESS] History context handled properly.")

@patch('app.services.ai_service.genai.Client')
def test_provider_failure(mock_client_cls, auth_client, app):
    print("\n--- Testing AI Provider Failure ---")
    mock_client_cls.return_value.chats.create.side_effect = Exception("Gemini API rate limit exceeded")
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "unexpected provider error" in resp.json['error'].lower()
    print("[SUCCESS] Provider failure caught gracefully.")

def test_empty_query(auth_client, app):
    print("\n--- Testing Empty Query ---")
    resp = auth_client.post('/api/agent/ask', json={})
    assert resp.status_code == 400
    assert "Query is required" in resp.json['error']
    print("[SUCCESS] Empty query rejected.")


@patch('app.services.ai_service.genai.Client')
def test_provider_429_quota_failure(mock_client_cls, auth_client, app):
    print("\n--- Testing AI Provider 429 Quota Failure ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    mock_chat.send_message.side_effect = Exception("429 Resource Exhausted: Quota exceeded")
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "Quota Exceeded" in resp.json['error']
    print("[SUCCESS] 429 Quota failure caught gracefully.")

@patch('app.services.ai_service.genai.Client')
def test_provider_503_timeout_failure(mock_client_cls, auth_client, app):
    print("\n--- Testing AI Provider 503 Timeout Failure ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    # It will retry up to max_retries, we patch time.sleep to run fast
    mock_chat.send_message.side_effect = Exception("503 Service Unavailable: High demand")
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    with patch('time.sleep', return_value=None):
        resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "high demand" in resp.json['error'] or "temporary timeout" in resp.json['error']
    print("[SUCCESS] 503 Timeout failure caught gracefully.")

@patch('app.services.ai_service.genai.Client')
def test_provider_401_auth_failure(mock_client_cls, auth_client, app):
    print("\n--- Testing AI Provider 401 Auth Failure ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    mock_chat.send_message.side_effect = Exception("401 Unauthorized: API_KEY_INVALID")
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "Invalid API Key" in resp.json['error']
    print("[SUCCESS] 401 Auth failure caught gracefully.")
