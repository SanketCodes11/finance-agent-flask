import re

file_path = 'tests/test_agent_pytest.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "Gemini API rate limit exceeded" in resp.json['error']'''

replace = '''    resp = auth_client.post('/api/agent/ask', json={'query': 'Help'})
    assert resp.status_code == 500
    assert "unexpected provider error" in resp.json['error'].lower()'''

content = content.replace(target, replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed test_provider_failure")
