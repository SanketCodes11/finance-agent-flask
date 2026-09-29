import os
import pytest
from app import create_app, db
from config import Config, TestConfig
import importlib
import config

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

def test_health_check(client):
    res = client.get('/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'

def test_config_production_secret_key(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.setenv('SECRET_KEY', '') # Empty string to bypass .env fallback since load_dotenv doesn't overwrite
    
    with pytest.raises(ValueError, match="No SECRET_KEY set for Flask application in production"):
        importlib.reload(config)
        
    # Reload config to normal state for subsequent tests
    monkeypatch.delenv('FLASK_ENV', raising=False)
    monkeypatch.setenv('SECRET_KEY', 'test-secret')
    importlib.reload(config)
