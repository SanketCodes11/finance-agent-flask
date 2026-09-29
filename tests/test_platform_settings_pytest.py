import pytest
from app import create_app, db
from app.models.user import User, AdminAuditLog
from app.models.finance import PlatformSetting
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        
        user = User(username='test', email='test@test.com', is_active=True)
        user.set_password('Password123')
        
        admin = User(username='admin', email='admin@test.com', is_admin=True, is_active=True)
        admin.set_password('Password123')
        
        db.session.add_all([user, admin])
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_settings_unauth(client):
    resp = client.get('/admin/settings')
    assert resp.status_code == 302
    
def test_settings_normal_user(client):
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'}, follow_redirects=True)
    resp = client.get('/admin/settings')
    assert resp.status_code == 403
    
def test_settings_admin_user(client, app):
    client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)
    resp = client.get('/admin/settings')
    assert resp.status_code == 200
    assert b'Platform Settings' in resp.data
    
    resp = client.post('/admin/settings', data={
        'maintenance_mode': 'on',
        'ai_analyst_enabled': ''
    }, follow_redirects=True)
    assert resp.status_code == 200
    
    with app.app_context():
        settings = PlatformSetting.get_settings()
        assert settings.maintenance_mode is True
        assert settings.ai_analyst_enabled is False

def test_maintenance_unauth(client, app):
    with app.app_context():
        settings = PlatformSetting.get_settings()
        settings.maintenance_mode = True
        db.session.commit()
        
    resp1 = client.get('/')
    assert resp1.status_code == 503
    
def test_maintenance_normal_user(client, app):
    with app.app_context():
        settings = PlatformSetting.get_settings()
        settings.maintenance_mode = True
        db.session.commit()
        
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'}, follow_redirects=True)
    resp2 = client.get('/dashboard')
    assert resp2.status_code == 503
    
def test_maintenance_admin_user(client, app):
    with app.app_context():
        settings = PlatformSetting.get_settings()
        settings.maintenance_mode = True
        db.session.commit()
        
    client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)
    resp3 = client.get('/dashboard')
    assert resp3.status_code == 200

def test_ai_disabled_normal(client, app):
    with app.app_context():
        settings = PlatformSetting.get_settings()
        settings.ai_analyst_enabled = False
        db.session.commit()
        
    client.post('/auth/login', data={'username': 'test', 'password': 'Password123'}, follow_redirects=True)
    resp = client.post('/api/agent/ask', json={'query': 'Hello'})
    assert resp.status_code == 403

def test_ai_disabled_admin(client, app):
    with app.app_context():
        settings = PlatformSetting.get_settings()
        settings.ai_analyst_enabled = False
        db.session.commit()
        
    client.post('/admin/login', data={'username': 'admin', 'password': 'Password123'}, follow_redirects=True)
    from unittest.mock import patch
    with patch('app.services.ai_service.genai.Client') as mock_client:
        mock_chat = mock_client.return_value.chats.create.return_value
        mock_chat.send_message.return_value.text = "Mock"
        import os
        os.environ['GEMINI_API_KEY'] = 'valid-key'
        
        resp_admin = client.post('/api/agent/ask', json={'query': 'Hello'})
        assert resp_admin.status_code == 200
