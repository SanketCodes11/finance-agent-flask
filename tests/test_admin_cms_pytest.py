import pytest
from app import create_app, db
from app.models.user import User, AdminAuditLog
from app.models.finance import CMSContent
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
def setup_users(app):
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', is_admin=True, is_active=True)
        admin.set_password('pass123')
        
        normal = User(username='normal', email='normal@test.com', is_admin=False, is_active=True)
        normal.set_password('pass123')
        
        db.session.add_all([admin, normal])
        db.session.commit()

def login(client, username, password, is_admin=False):
    endpoint = '/admin/login' if is_admin else '/auth/login'
    return client.post(endpoint, data={'username': username, 'password': password}, follow_redirects=True)

def test_cms_access_denied(client, setup_users):
    # Unauthenticated
    res = client.get('/admin/cms')
    assert res.status_code == 403
    
    # Normal user
    login(client, 'normal', 'pass123')
    res = client.get('/admin/cms')
    assert res.status_code == 403

def test_cms_access_allowed_and_update(client, setup_users, app):
    login(client, 'admin', 'pass123', is_admin=True)
    
    # Access CMS page
    res = client.get('/admin/cms')
    assert res.status_code == 200
    assert b'Homepage Content Editor' in res.data
    
    # Update CMS Content
    new_title = 'Welcome to the New Super Awesome Platform!'
    new_subtitle = 'This is a brand new description updated via the Admin CMS.'
    
    res = client.post('/admin/cms', data={
        'cms_homepage_title': new_title,
        'cms_homepage_subtitle': new_subtitle
    }, follow_redirects=True)
    
    assert res.status_code == 200
    assert b'Content successfully updated' in res.data
    
    # Verify in DB
    with app.app_context():
        title_item = CMSContent.query.filter_by(key='homepage_title').first()
        assert title_item is not None
        assert title_item.value == new_title
        
        # Verify Audit Log
        u = User.query.filter_by(username='admin').first()
        log = AdminAuditLog.query.filter_by(admin_id=u.id, action='update_cms').first()
        assert log is not None
        assert 'homepage_title' in log.details

def test_public_homepage_reflects_cms_update(client, setup_users, app):
    # Before update, should have default or nothing
    res = client.get('/')
    assert res.status_code == 200
    assert b'Smarter Investing with <span class="text-primary">AI Insights</span>' in res.data
    
    # Admin logs in and updates
    login(client, 'admin', 'pass123', is_admin=True)
    new_title = 'TESTING LIVE CMS TITLE UPDATE'
    client.post('/admin/cms', data={
        'cms_homepage_title': new_title,
        'cms_homepage_subtitle': 'New subtitle'
    }, follow_redirects=True)
    
    # Logout so we can test the public view properly (though not strictly necessary as index redirects authenticated users to dashboard)
    client.get('/auth/logout')
    
    # Test the public homepage
    res = client.get('/')
    assert res.status_code == 200
    assert new_title.encode() in res.data
