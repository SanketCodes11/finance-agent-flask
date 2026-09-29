import os

file_path = 'app/templates/paper_trading.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

js_target = '''        document.getElementById('tradeForm').addEventListener('submit', function(e) {
            e.preventDefault();
            executeTrade();
        });'''

js_replacement = '''        document.getElementById('tradeForm').addEventListener('submit', function(e) {
            e.preventDefault();
            executeTrade();
        });

        document.getElementById('walletForm').addEventListener('submit', function(e) {
            e.preventDefault();
            executeWalletAction();
        });'''

content = content.replace(js_target, js_replacement)

js_target2 = '''    function loadHistory() {'''
js_replacement2 = '''    let walletModal;
    document.addEventListener('DOMContentLoaded', function() {
        walletModal = new bootstrap.Modal(document.getElementById('walletModal'));
    });

    function openWalletModal(action) {
        document.getElementById('walletAction').value = action;
        document.getElementById('walletAmount').value = '';
        document.getElementById('walletAlert').innerHTML = '';
        document.getElementById('walletBtnText').textContent = action === 'DEPOSIT' ? 'Add Funds' : 'Withdraw Funds';
        document.getElementById('walletModalTitle').innerHTML = action === 'DEPOSIT' ? '<i class="fa-solid fa-arrow-down text-success me-2"></i>Add Funds' : '<i class="fa-solid fa-arrow-up text-secondary me-2"></i>Withdraw Funds';
        
        // Ensure cash balance is up to date
        const currentCashText = document.getElementById('cashBalance').textContent;
        document.getElementById('walletCurrentBalance').textContent = currentCashText;
    }

    function executeWalletAction() {
        const action = document.getElementById('walletAction').value;
        const amount = parseFloat(document.getElementById('walletAmount').value);
        
        const btn = document.getElementById('walletBtn');
        const spinner = document.getElementById('walletSpinner');
        const alertBox = document.getElementById('walletAlert');
        
        btn.disabled = true;
        spinner.classList.remove('d-none');
        alertBox.innerHTML = '';

        fetch('/api/paper-trade/wallet', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                action: action,
                amount: amount
            })
        })
        .then(async res => {
            const data = await res.json();
            if (!res.ok) throw data;
            return data;
        })
        .then(data => {
            alertBox.innerHTML = `<div class="alert alert-success border-success text-success px-3 py-2 rounded-3 small fw-medium"><i class="fa-solid fa-check-circle me-1"></i> ${data.message}</div>`;
            document.getElementById('walletForm').reset();
            loadAccount();
            loadWalletHistory();
            setTimeout(() => walletModal.hide(), 1500);
        })
        .catch(err => {
            alertBox.innerHTML = `<div class="alert alert-danger border-danger text-danger px-3 py-2 rounded-3 small fw-medium"><i class="fa-solid fa-circle-exclamation me-1"></i> ${err.error || 'Failed to process transaction'}</div>`;
        })
        .finally(() => {
            btn.disabled = false;
            spinner.classList.add('d-none');
        });
    }

    function loadWalletHistory() {
        fetch('/api/paper-trade/wallet/history')
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('walletHistoryTableBody');
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="text-center py-5 text-muted">No wallet transactions found.</td></tr>';
                    return;
                }
                
                let html = '';
                data.forEach(item => {
                    const date = new Date(item.timestamp).toLocaleString();
                    const badgeClass = item.type === 'DEPOSIT' ? 'bg-success-subtle text-success' : 'bg-secondary-subtle text-secondary';
                    const sign = item.type === 'DEPOSIT' ? '+' : '-';
                    html += `
                        <tr>
                            <td class="ps-4 text-muted small">${date}</td>
                            <td><span class="badge ${badgeClass}">${item.type}</span></td>
                            <td class="text-muted small">${item.description || ''}</td>
                            <td class="fw-bold ${item.type === 'DEPOSIT' ? 'text-success' : ''}">${sign}$${item.amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                            <td class="pe-4 text-end fw-medium">$${item.balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
            });
    }

    function loadHistory() {
        loadWalletHistory();'''

content = content.replace(js_target2, js_replacement2)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
