import os

path = os.path.abspath('tests/test_transactions_pytest.py')
with open(path, 'r', encoding='utf-8') as f:
    original = f.read()

fixtures = """import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig
from unittest.mock import patch

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class AuthActions:
    def __init__(self, client):
        self.client = client
    def login(self, username='testuser', password='Password123'):
        return self.client.post('/auth/login', data={'username': username, 'password': password})
    def logout(self):
        return self.client.get('/auth/logout')

@pytest.fixture
def auth(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
    return AuthActions(client)

@pytest.fixture
def mock_quote():
    with patch('app.api.finance.get_stock_quote') as mock:
        mock.return_value = {
            'price': 150.0,
            'name': 'Apple Inc.',
            'currency': 'USD',
            'change': 2.5,
            'change_percent': 1.6
        }
        yield mock
"""

# Replace "import pytest" with the full block of fixtures
new_content = original.replace("import pytest\n", fixtures + "\n")

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Added fixtures to test_transactions_pytest.py")
