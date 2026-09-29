import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """@pytest.fixture
def normal_client(client, app):
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'})
    return client

@pytest.fixture
def admin_client(client, app):
    client.post('/auth/login', data={'username': 'admin', 'password': 'Password123'})
    return client"""

replace = """@pytest.fixture
def normal_client(app):
    c = app.test_client()
    c.post('/auth/login', data={'username': 'test', 'password': 'Password123'})
    return c

@pytest.fixture
def admin_client(app):
    c = app.test_client()
    c.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})
    return c"""

content = content.replace(target, replace)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed separate clients.")
