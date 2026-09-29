import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "admin_client.post('/auth/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)",
    "admin_client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)"
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed admin login route.")
