import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """@pytest.fixture
def admin_client(app):
    c = app.test_client()
    c.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})
    return c"""

replace = """@pytest.fixture
def admin_client(app):
    c = app.test_client()
    resp = c.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})
    print("Admin login response:", resp.status_code, resp.location, resp.data)
    return c"""

content = content.replace(target, replace)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Added debug to admin_client.")
