import os

for filename in ['tests/test_admin_dashboard_pytest.py', 'tests/test_admin_activity_pytest.py']:
    with open(filename, 'r') as f:
        content = f.read()
        
    old_login = """def login(client, username, password):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)"""
    
    new_login = """def login(client, username, password, is_admin=False):
    endpoint = '/admin/login' if is_admin else '/auth/login'
    return client.post(endpoint, data={'username': username, 'password': password}, follow_redirects=True)"""
    
    if old_login in content:
        content = content.replace(old_login, new_login)
        content = content.replace("login(client, 'admin', 'pass123')", "login(client, 'admin', 'pass123', is_admin=True)")
        with open(filename, 'w') as f:
            f.write(content)
