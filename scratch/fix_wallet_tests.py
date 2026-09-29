import os

file_path = 'tests/test_paper_trading_pytest.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('(client, setup_users, auth_headers):', '(client, auth):')
content = content.replace(', headers=auth_headers', '')
content = content.replace("    client.get('/api/paper-trade/account')", "    auth.login()\n    client.get('/api/paper-trade/account')")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
