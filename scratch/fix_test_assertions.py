import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target1 = """            resp = normal_client.get('/admin/settings')
            assert resp.status_code == 302"""
replace1 = """            resp = normal_client.get('/admin/settings')
            assert resp.status_code == 403"""

target2 = """            resp = normal_client.post('/api/agent/ask', json={'query': 'Hello'})
            assert resp.status_code == 302"""
replace2 = """            resp = normal_client.post('/api/agent/ask', json={'query': 'Hello'})
            assert resp.status_code == 403"""

target3 = """        with app.test_client() as admin_client:
            admin_client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)
            resp3 = admin_client.get('/dashboard')
            assert resp3.status_code == 200"""
replace3 = """        with app.test_client() as admin_client:
            resp_login = admin_client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)
            if b'Invalid username or password' in resp_login.data: print('ADMIN LOGIN FAILED!')
            resp3 = admin_client.get('/dashboard')
            assert resp3.status_code == 200"""

content = content.replace(target1, replace1)
content = content.replace(target2, replace2)
content = content.replace(target3, replace3)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
