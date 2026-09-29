import os
import re

path = os.path.abspath('app/templates/portfolio.html')
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# I want to add the Transaction History table at the bottom, and update the Add Holding modal to Transaction modal.

transaction_history_html = """
    <!-- Transaction History Section -->
    <div class="row mt-5">
        <div class="col-12">
            <h4 class="fw-bold tracking-tight mb-4">Transaction History</h4>
            <div class="card border-0 shadow-sm rounded-4 premium-card">
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead class="bg-light">
                                <tr>
                                    <th class="ps-4 text-muted fw-semibold small text-uppercase">Date</th>
                                    <th class="text-muted fw-semibold small text-uppercase">Type</th>
                                    <th class="text-muted fw-semibold small text-uppercase">Symbol</th>
                                    <th class="text-muted fw-semibold small text-uppercase text-end">Quantity</th>
                                    <th class="text-muted fw-semibold small text-uppercase text-end">Price</th>
                                    <th class="text-muted fw-semibold small text-uppercase text-end">Value</th>
                                    <th class="pe-4 text-muted fw-semibold small text-uppercase text-end">Realized P/L</th>
                                </tr>
                            </thead>
                            <tbody id="txTableBody">
                                <tr>
                                    <td colspan="7" class="text-center py-4 text-muted">Loading transactions...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
"""

# Find the end of the portfolio table section to insert the transaction history
table_end_marker = "</div>\n    </div>\n</div>\n" # This is tricky, let's find a reliable anchor.
# A good anchor is before "<!-- Add Holding Modal -->"

anchor = "<!-- Add Holding Modal -->"
if anchor in content:
    content = content.replace(anchor, transaction_history_html + "\n\n" + anchor)

# Replace the Add Holding Modal title to "Add Transaction"
content = content.replace("Add Holding", "New Transaction")
content = content.replace("Add your first holding", "Add your first transaction")

# We need to add "Transaction Type" to the modal.
modal_body_marker = '<div class="mb-3">\n                            <label for="symbolInput" class="form-label fw-medium">Stock Symbol</label>'
new_modal_fields = """<div class="mb-3">
                            <label class="form-label fw-medium">Transaction Type</label>
                            <select class="form-select bg-body-tertiary border-0 px-3 py-2" id="txTypeInput" required>
                                <option value="BUY" selected>BUY</option>
                                <option value="SELL">SELL</option>
                            </select>
                        </div>\n                        <div class="mb-3">
                            <label for="symbolInput" class="form-label fw-medium">Stock Symbol</label>"""
content = content.replace(modal_body_marker, new_modal_fields)

# Modify Javascript
js_submit = """const payload = {
                symbol: document.getElementById('symbolInput').value,
                quantity: parseFloat(document.getElementById('qtyInput').value),
                purchase_price: parseFloat(document.getElementById('priceInput').value),
                purchase_date: document.getElementById('dateInput').value,
                transaction_type: document.getElementById('txTypeInput').value
            };"""

old_js_submit = """const payload = {
                symbol: document.getElementById('symbolInput').value,
                quantity: parseFloat(document.getElementById('qtyInput').value),
                purchase_price: parseFloat(document.getElementById('priceInput').value),
                purchase_date: document.getElementById('dateInput').value
            };"""
content = content.replace(old_js_submit, js_submit)

# Add loadTransactions in fetchPortfolio
js_fetch_portfolio = "fetchPortfolio();"
js_fetch_portfolio_new = "fetchPortfolio();\n        fetchTransactions();"

# We should add fetchTransactions function to JS
fetch_tx_js = """
    function fetchTransactions() {
        fetch('/api/portfolio/transactions')
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById('txTableBody');
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No transactions found.</td></tr>';
                    return;
                }
                tbody.innerHTML = '';
                data.forEach(tx => {
                    const tr = document.createElement('tr');
                    const isBuy = tx.type === 'BUY';
                    const typeBadge = `<span class="badge ${isBuy ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-danger-subtle text-danger border border-danger-subtle'} rounded-pill">${tx.type}</span>`;
                    
                    let plStr = '--';
                    if (tx.realized_pl !== null) {
                        const isPos = tx.realized_pl >= 0;
                        plStr = `<span class="${isPos ? 'text-success' : 'text-danger'} fw-bold">${isPos ? '+' : ''}${tx.realized_pl.toFixed(2)}</span>`;
                    }

                    tr.innerHTML = `
                        <td class="ps-4 text-muted">${tx.date}</td>
                        <td>${typeBadge}</td>
                        <td class="fw-bold">${tx.symbol}</td>
                        <td class="text-end">${tx.quantity}</td>
                        <td class="text-end">${tx.price.toFixed(2)}</td>
                        <td class="text-end fw-medium">${tx.total_value.toFixed(2)}</td>
                        <td class="pe-4 text-end">${plStr}</td>
                    `;
                    tbody.appendChild(tr);
                });
            })
            .catch(err => console.error("Error fetching transactions:", err));
    }
"""

content = content.replace("function renderPortfolio() {", fetch_tx_js + "\n    function renderPortfolio() {")
content = content.replace("fetchPortfolio();\n    });\n</script>", "fetchPortfolio();\n        fetchTransactions();\n    });\n</script>")
content = content.replace("fetchPortfolio();\n                  }", "fetchPortfolio();\n                      fetchTransactions();\n                  }")


with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Rewrote portfolio.html.")
