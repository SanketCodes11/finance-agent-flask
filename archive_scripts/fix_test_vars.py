import os

path = os.path.abspath('tests/test_alerts_pytest.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('test_user(mock_quotes, app, test_user):', 'test_user_dummy()') # Oops, didn't exist
content = content.replace(', test_user):', ', test_user_id):')
content = content.replace('test_user.id', 'test_user_id')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed test arguments.")
