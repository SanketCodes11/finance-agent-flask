import pytest
import os
import base64
from datetime import date
from app import create_app, db
from app.models.user import User
from app.models.finance import FinancialGoal
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test data
        u = User(username='testadmin', email='testadmin@test.com')
        u.set_password('supersecret')
        db.session.add(u)
        
        goal = FinancialGoal(user_id=1, name='Test Goal', target_amount=1000, target_date=date(2030,1,1))
        db.session.add(goal)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def get_auth_headers(username, password):
    auth_str = f"{username}:{password}"
    b64_auth = base64.b64encode(auth_str.encode()).decode('utf-8')
    return {'Authorization': f'Basic {b64_auth}'}

def test_admin_db_unauthorized(client):
    res = client.get('/admin/db')
    assert res.status_code == 401
    assert b'Basic realm="Admin Login Required"' in res.headers.get('WWW-Authenticate', b'').encode()

def test_admin_db_wrong_credentials(client, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'admin123')
    
    headers = get_auth_headers('admin', 'wrongpass')
    res = client.get('/admin/db', headers=headers)
    assert res.status_code == 401

def test_admin_db_authorized(client, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'admin123')
    
    headers = get_auth_headers('admin', 'admin123')
    res = client.get('/admin/db', headers=headers)
    assert res.status_code == 200
    # Check if a table like user or financial_goal is listed
    assert b'user' in res.data
    assert b'financial_goal' in res.data

def test_admin_db_table_view(client, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'admin123')
    
    headers = get_auth_headers('admin', 'admin123')
    res = client.get('/admin/db?table=user', headers=headers)
    assert res.status_code == 200
    
    # Sensitive column shouldn't be in the HTML
    assert b'password_hash' not in res.data
    assert b'supersecret' not in res.data
    
    # Normal columns should be there
    assert b'testadmin' in res.data
    assert b'testadmin@test.com' in res.data

def test_admin_db_search(client, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'admin123')
    
    headers = get_auth_headers('admin', 'admin123')
    # Search for Test Goal
    res = client.get('/admin/db?table=financial_goal&q=Test+Goal', headers=headers)
    assert res.status_code == 200
    assert b'Test Goal' in res.data
    
    # Search for something not there
    res = client.get('/admin/db?table=financial_goal&q=NonExistent', headers=headers)
    assert res.status_code == 200
    assert b'No records found' in res.data

def test_admin_db_disabled_in_production(client, monkeypatch):
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD', 'admin123')
    monkeypatch.setenv('FLASK_ENV', 'production')
    
    headers = get_auth_headers('admin', 'admin123')
    res = client.get('/admin/db', headers=headers)
    assert res.status_code == 404
