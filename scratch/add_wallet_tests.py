import os

file_path = 'tests/test_paper_trading_pytest.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

wallet_tests = '''
def test_wallet_deposit(client, setup_users, auth_headers):
    # Load account to initialize it
    client.get('/api/paper-trade/account', headers=auth_headers)
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': 50000
    }, headers=auth_headers)
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['new_balance'] == 1050000.0
    
    # Check history
    res = client.get('/api/paper-trade/wallet/history', headers=auth_headers)
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['type'] == 'DEPOSIT'
    assert data[0]['amount'] == 50000

def test_wallet_withdraw_success(client, setup_users, auth_headers):
    client.get('/api/paper-trade/account', headers=auth_headers)
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'WITHDRAW',
        'amount': 100000
    }, headers=auth_headers)
    
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['new_balance'] == 900000.0

def test_wallet_withdraw_insufficient_funds(client, setup_users, auth_headers):
    client.get('/api/paper-trade/account', headers=auth_headers)
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'WITHDRAW',
        'amount': 2000000 # More than initial 1,000,000
    }, headers=auth_headers)
    
    assert res.status_code == 400
    assert 'Insufficient available cash' in res.get_json()['error']

def test_wallet_invalid_amount(client, setup_users, auth_headers):
    client.get('/api/paper-trade/account', headers=auth_headers)
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': -500
    }, headers=auth_headers)
    assert res.status_code == 400
    
    res = client.post('/api/paper-trade/wallet', json={
        'action': 'DEPOSIT',
        'amount': 'invalid'
    }, headers=auth_headers)
    assert res.status_code == 400
'''

if 'test_wallet_deposit' not in content:
    content += wallet_tests
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
