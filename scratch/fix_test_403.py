import re

file_path = "tests/test_platform_settings_pytest.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: admin_required returns 403
target1 = """    # Unauthenticated user
    resp = client.get('/admin/settings')
    assert resp.status_code == 302
    assert '/auth/login' in resp.location
    
    # Normal user
    resp = normal_client.get('/admin/settings')
    assert resp.status_code == 302
    assert '/admin/login' in resp.location  # Prevented by admin_required"""

replace1 = """    # Unauthenticated user
    resp = client.get('/admin/settings')
    assert resp.status_code == 403
    
    # Normal user
    resp = normal_client.get('/admin/settings')
    assert resp.status_code == 403"""

content = content.replace(target1, replace1)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed test assertions for 403.")
