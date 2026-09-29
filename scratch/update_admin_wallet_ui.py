import os

# 1. Fetch wallet txs in admin route
file_path = 'app/routes/admin.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    virtual_orders = VirtualOrder.query.filter_by(account_id=virtual_account.id).order_by(VirtualOrder.created_at.desc()).limit(10).all() if virtual_account else []'''
replacement = '''    virtual_orders = VirtualOrder.query.filter_by(account_id=virtual_account.id).order_by(VirtualOrder.timestamp.desc()).limit(10).all() if virtual_account else []
    
    from app.models.finance import VirtualWalletTransaction
    wallet_txs = VirtualWalletTransaction.query.filter_by(account_id=virtual_account.id).order_by(VirtualWalletTransaction.timestamp.desc()).limit(10).all() if virtual_account else []'''

if 'wallet_txs = VirtualWallet' not in content:
    content = content.replace(target, replacement)
    
    target_render = '''                           virtual_account=virtual_account,
                           virtual_orders=virtual_orders,'''
    replace_render = '''                           virtual_account=virtual_account,
                           virtual_orders=virtual_orders,
                           wallet_txs=wallet_txs,'''
    content = content.replace(target_render, replace_render)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# 2. Update user_detail.html
file_path = 'app/templates/admin/user_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

target_html = '''                    <h6 class="fw-bold mb-3">Recent Virtual Orders</h6>'''
replace_html = '''                    <div class="row mb-3">
                        <div class="col-md-6">
                            <h6 class="fw-bold">Virtual Account Cash Balance: <span class="text-success">${% if virtual_account %}{{ "{:,.2f}".format(virtual_account.current_cash) }}{% else %}0.00{% endif %}</span></h6>
                        </div>
                    </div>
                    <div class="row">
                    <div class="col-md-6">
                    <h6 class="fw-bold mb-3">Recent Virtual Orders</h6>'''

if '<h6 class="fw-bold">Virtual Account Cash Balance:' not in html_content:
    html_content = html_content.replace(target_html, replace_html)

    target_table_end = '''                    {% else %}
                    <div class="text-center py-5 text-muted">
                        <p>No paper trading activity found.</p>
                    </div>
                    {% endif %}
                </div>'''

    replace_table_end = '''                    {% else %}
                    <div class="text-center py-5 text-muted">
                        <p>No paper trading activity found.</p>
                    </div>
                    {% endif %}
                    </div>
                    <div class="col-md-6">
                        <h6 class="fw-bold mb-3">Wallet Transactions (Deposits/Withdrawals)</h6>
                        {% if wallet_txs %}
                        <div class="table-responsive">
                            <table class="table table-sm align-middle">
                                <thead>
                                    <tr>
                                        <th>Date</th>
                                        <th>Type</th>
                                        <th>Amount</th>
                                        <th>Resulting Balance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for tx in wallet_txs %}
                                    <tr>
                                        <td class="text-muted small">{{ tx.timestamp.strftime('%Y-%m-%d %H:%M') }}</td>
                                        <td><span class="badge {% if tx.transaction_type == 'DEPOSIT' %}bg-success{% else %}bg-secondary{% endif %}">{{ tx.transaction_type }}</span></td>
                                        <td>${{ "{:,.2f}".format(tx.amount) }}</td>
                                        <td>${{ "{:,.2f}".format(tx.resulting_balance) }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                        {% else %}
                        <div class="text-center py-5 text-muted">
                            <p>No wallet transactions found.</p>
                        </div>
                        {% endif %}
                    </div>
                    </div>
                </div>'''

    html_content = html_content.replace(target_table_end, replace_table_end)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
