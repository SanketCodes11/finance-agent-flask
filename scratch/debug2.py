import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """@pytest.fixture
def admin_client(app):
    c = app.test_client()
    resp = c.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})
    print("Admin login response:", resp.status_code, resp.location, resp.data)
    return c"""

replace = """@pytest.fixture
def admin_client(app):
    c = app.test_client()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        print("Admin user from DB:", admin.username, "is_admin:", admin.is_admin, "is_active:", getattr(admin, 'is_active', 'N/A'))
    
    resp = c.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})
    print("Admin login response:", resp.status_code, resp.location)
    return c"""

content = content.replace(target, replace)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated debug info.")
