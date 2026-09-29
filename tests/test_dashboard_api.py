import pytest
from app import create_app, db
from app.models.user import User
from config import TestConfig

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

@pytest.fixture
def auth_client(client, app):
    with app.app_context():
        user = User(username='testuser', email='test@test.com')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()
    client.post('/auth/login', data={'username': 'testuser', 'password': 'Password123'})
    return client

from unittest.mock import patch

@patch('app.services.finance_service.get_multiple_stock_quotes')
def test_market_indices(mock_multiple, auth_client):
    mock_multiple.return_value = {
        'SPY': {'symbol': 'SPY', 'price': 500.0, 'name': 'S&P 500 (SPY)'}
    }
    res = auth_client.get('/api/market_indices')
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]['symbol'] == 'SPY'
    # verify SPY is in there
    symbols = [item['symbol'] for item in data]
    assert 'SPY' in symbols
