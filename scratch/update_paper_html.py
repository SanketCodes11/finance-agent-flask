import os

file_path = 'app/templates/paper_trading.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add buttons under the Available Cash card
cash_replacement = '''
                    <p class="text-muted mb-1 small fw-medium text-uppercase tracking-wide">Available Cash</p>
                    <h3 class="fw-bold mb-3" id="cashBalance">Loading...</h3>
                    <div class="d-flex justify-content-center gap-2">
                        <button class="btn btn-sm btn-outline-success fw-medium rounded-pill px-3" data-bs-toggle="modal" data-bs-target="#walletModal" onclick="openWalletModal('DEPOSIT')">
                            <i class="fa-solid fa-arrow-down me-1"></i> Add Funds
                        </button>
                        <button class="btn btn-sm btn-outline-secondary fw-medium rounded-pill px-3" data-bs-toggle="modal" data-bs-target="#walletModal" onclick="openWalletModal('WITHDRAW')">
                            <i class="fa-solid fa-arrow-up me-1"></i> Withdraw
                        </button>
                    </div>
'''
content = content.replace('''
                    <p class="text-muted mb-1 small fw-medium text-uppercase tracking-wide">Available Cash</p>
                    <h3 class="fw-bold mb-0" id="cashBalance">Loading...</h3>''', cash_replacement)

# Add Wallet Modal
wallet_modal = '''
<!-- Wallet Modal -->
<div class="modal fade" id="walletModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content border-0 shadow-lg rounded-4 overflow-hidden">
            <div class="modal-header border-bottom-0 bg-light pb-0">
                <h5 class="modal-title fw-bold" id="walletModalTitle"><i class="fa-solid fa-wallet text-primary me-2"></i>Manage Funds</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body p-4 pt-3">
                <form id="walletForm">
                    <input type="hidden" id="walletAction">
                    <div id="walletAlert"></div>
                    <div class="mb-3 text-center">
                        <p class="text-muted small mb-2">Available Balance</p>
                        <h4 class="fw-bold" id="walletCurrentBalance">$0.00</h4>
                    </div>
                    <div class="mb-4">
                        <label class="form-label fw-bold">Amount</label>
                        <div class="input-group input-group-lg shadow-sm">
                            <span class="input-group-text bg-white border-end-0 text-muted">$</span>
                            <input type="number" class="form-control border-start-0" id="walletAmount" min="1" step="0.01" required>
                        </div>
                    </div>
                    <div class="d-flex gap-2 mb-4">
                        <button type="button" class="btn btn-outline-secondary flex-grow-1" onclick="document.getElementById('walletAmount').value=10000">+$10k</button>
                        <button type="button" class="btn btn-outline-secondary flex-grow-1" onclick="document.getElementById('walletAmount').value=50000">+$50k</button>
                        <button type="button" class="btn btn-outline-secondary flex-grow-1" onclick="document.getElementById('walletAmount').value=100000">+$100k</button>
                    </div>
                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary btn-lg rounded-pill fw-medium shadow-sm" id="walletBtn">
                            <span class="spinner-border spinner-border-sm d-none me-2" id="walletSpinner" role="status" aria-hidden="true"></span>
                            <span id="walletBtnText">Submit</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
'''

content = content.replace('<!-- Trade Modal -->', wallet_modal + '\n<!-- Trade Modal -->')

# Update the History section to have Tabs for Trades and Wallet
history_section_target = '''<div class="card border-0 shadow-sm rounded-4 premium-card">
        <div class="card-header bg-transparent border-bottom py-3 px-4 d-flex justify-content-between align-items-center">
            <h5 class="fw-bold mb-0">Order History</h5>
        </div>'''
history_section_replace = '''<div class="card border-0 shadow-sm rounded-4 premium-card">
        <div class="card-header bg-transparent border-bottom pt-3 pb-0 px-4">
            <ul class="nav nav-tabs border-bottom-0" id="historyTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active fw-medium" id="trades-tab" data-bs-toggle="tab" data-bs-target="#trades" type="button" role="tab">Trades</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link fw-medium" id="wallet-tx-tab" data-bs-toggle="tab" data-bs-target="#wallet-tx" type="button" role="tab">Wallet Transfers</button>
                </li>
            </ul>
        </div>
        <div class="card-body p-0">
            <div class="tab-content" id="historyTabsContent">
                <div class="tab-pane fade show active" id="trades" role="tabpanel">
'''

content = content.replace(history_section_target, history_section_replace)

# Need to close the tab pane and add the wallet tab pane
table_close_target = '''            </div>
        </div>
    </div>'''
table_close_replace = '''            </div>
                </div>
                <div class="tab-pane fade" id="wallet-tx" role="tabpanel">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th class="ps-4">Date</th>
                                    <th>Type</th>
                                    <th>Description</th>
                                    <th>Amount</th>
                                    <th class="pe-4 text-end">Resulting Balance</th>
                                </tr>
                            </thead>
                            <tbody id="walletHistoryTableBody">
                                <tr>
                                    <td colspan="5" class="text-center py-5 text-muted">Loading...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>'''

content = content.replace(table_close_target, table_close_replace)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
