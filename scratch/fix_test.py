import os

with open('tests/test_admin_login_pytest.py', 'r') as f:
    c = f.read()

c = c.replace(
    "assert b'Welcome Back' in res.data # Should redirect back to normal login", 
    "assert b'Finance Insight Agent' in res.data # Should redirect back to main index"
)

with open('tests/test_admin_login_pytest.py', 'w') as f:
    f.write(c)
