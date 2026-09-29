import re

file_path = 'tests/test_agent_pytest.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''def test_missing_api_key(client, app):
    print("\\n--- Testing Missing Gemini API Key ---")
    app.config['GEMINI_API_KEY'] = 'your-gemini-api-key-here' # Unconfigured fallback state
    import os
    os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
    with app.app_context():
        res = fetch_agent_insight("Hello")
        assert "not configured" in res.lower()
        print("[SUCCESS] Missing API key handled safely without crashing.")'''

replace = '''def test_missing_api_key(client, app):
    print("\\n--- Testing Missing Gemini API Key ---")
    app.config['GEMINI_API_KEY'] = 'your-gemini-api-key-here' # Unconfigured fallback state
    import os
    os.environ['GEMINI_API_KEY'] = 'your-gemini-api-key-here'
    with app.app_context():
        with pytest.raises(Exception) as exc:
            fetch_agent_insight("Hello")
        assert "not configured" in str(exc.value).lower()
        print("[SUCCESS] Missing API key handled safely.")'''

content = content.replace(target, replace)

# Add new tests
new_tests = '''

@patch('app.services.ai_service.genai.Client')
def test_provider_429_quota_failure(mock_client_cls, auth_client, app):
    print("\\n--- Testing AI Provider 429 Quota Failure ---")
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
    print("\\n--- Testing AI Provider 503 Timeout Failure ---")
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
    print("\\n--- Testing AI Provider 401 Auth Failure ---")
    mock_chat = mock_client_cls.return_value.chats.create.return_value
    mock_chat.send_message.side_effect = Exception("401 Unauthorized: API_KEY_INVALID")
    
    import os
    os.environ['GEMINI_API_KEY'] = 'valid-key'
    
    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "Invalid API Key" in resp.json['error']
    print("[SUCCESS] 401 Auth failure caught gracefully.")
'''
content += new_tests

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added new tests to test_agent_pytest.py")
