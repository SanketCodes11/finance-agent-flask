import pytest
from app import create_app, db
from app.models.finance import Alert
from app.models.user import User
from app.services.alert_service import check_active_alerts
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
def test_user_id(app):
    with app.app_context():
        user = User(username='test_user', email='test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return user.id

@patch('app.services.alert_service.get_multiple_stock_quotes')
def test_alert_above_triggers(mock_quotes, app, test_user_id):
    with app.app_context():
        alert = Alert(user_id=test_user_id, symbol='AAPL', condition='above', target_price=150.0)
        db.session.add(alert)
        db.session.commit()
        
        mock_quotes.return_value = {'AAPL': {'price': 149.0}}
        check_active_alerts(app)
        
        db.session.expire_all()
        alert = db.session.get(Alert, alert.id)
        assert alert.is_active == True
        assert alert.triggered_at is None
        
        mock_quotes.return_value = {'AAPL': {'price': 151.0}}
        check_active_alerts(app)
        
        db.session.expire_all()
        alert = db.session.get(Alert, alert.id)
        assert alert.is_active == False
        assert alert.triggered_at is not None

@patch('app.services.alert_service.get_multiple_stock_quotes')
def test_alert_below_triggers(mock_quotes, app, test_user_id):
    with app.app_context():
        alert = Alert(user_id=test_user_id, symbol='MSFT', condition='below', target_price=100.0)
        db.session.add(alert)
        db.session.commit()
        
        mock_quotes.return_value = {'MSFT': {'price': 101.0}}
        check_active_alerts(app)
        
        db.session.expire_all()
        alert = db.session.get(Alert, alert.id)
        assert alert.is_active == True
        
        mock_quotes.return_value = {'MSFT': {'price': 99.0}}
        check_active_alerts(app)
        
        db.session.expire_all()
        alert = db.session.get(Alert, alert.id)
        assert alert.is_active == False

@patch('app.services.alert_service.get_multiple_stock_quotes')
def test_alert_api_failure_handling(mock_quotes, app, test_user_id):
    with app.app_context():
        alert1 = Alert(user_id=test_user_id, symbol='AAPL', condition='above', target_price=150.0)
        alert2 = Alert(user_id=test_user_id, symbol='TSLA', condition='above', target_price=50.0)
        db.session.add_all([alert1, alert2])
        db.session.commit()
        
        mock_quotes.return_value = {'AAPL': {'price': None}, 'TSLA': {'price': 55.0}}
        check_active_alerts(app)
        
        db.session.expire_all()
        a1 = db.session.get(Alert, alert1.id)
        a2 = db.session.get(Alert, alert2.id)
        
        assert a1.is_active == True
        assert a2.is_active == False

@patch('app.services.alert_service.get_multiple_stock_quotes')
def test_alert_network_failure(mock_quotes, app, test_user_id):
    with app.app_context():
        alert = Alert(user_id=test_user_id, symbol='AAPL', condition='above', target_price=150.0)
        db.session.add(alert)
        db.session.commit()
        
        mock_quotes.side_effect = Exception("Network timeout")
        check_active_alerts(app)
        
        db.session.expire_all()
        a = db.session.get(Alert, alert.id)
        assert a.is_active == True
