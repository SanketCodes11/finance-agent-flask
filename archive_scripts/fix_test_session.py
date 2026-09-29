import os

path = os.path.abspath('tests/test_alerts_pytest.py')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("check_active_alerts(app)\n\n        alert = db.session.get(Alert, alert.id)", "check_active_alerts(app)\n        db.session.expire_all()\n        alert = db.session.get(Alert, alert.id)")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Added expire_all()")
