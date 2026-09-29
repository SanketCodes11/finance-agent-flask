import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the 403 back to 302
content = content.replace("assert resp.status_code == 403", "assert resp.status_code == 302")

# Let's add follow_redirects=True for login so we can see the final page!
# And let's assert what the final page is.
target = "admin_client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'})"
replace = "admin_client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)"

content = content.replace(target, replace)

# Same for normal_client
target2 = "normal_client.post('/auth/login', data={'username': 'test', 'password': 'Password123'})"
replace2 = "normal_client.post('/auth/login', data={'username': 'test', 'password': 'Password123'}, follow_redirects=True)"

content = content.replace(target2, replace2)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated to follow redirects and assert 302 for unauth.")
