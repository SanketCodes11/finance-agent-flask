import os

templates = {
    'comparison.html': """{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-0">
    <h2 class="fw-bold tracking-tight mb-4">Stock Comparison</h2>
    <div class="card border-0 shadow-sm rounded-4 premium-card mb-4">
        <div class="card-body p-4">
            <div class="row g-3 align-items-end">
                <div class="col-md-4">
                    <label class="form-label fw-medium text-muted">Stock 1 (e.g. AAPL)</label>
                    <input type="text" id="sym1" class="form-control rounded-pill bg-body-tertiary border-0 px-4" placeholder="Symbol 1">
                </div>
                <div class="col-md-4">
                    <label class="form-label fw-medium text-muted">Stock 2 (e.g. MSFT)</label>
                    <input type="text" id="sym2" class="form-control rounded-pill bg-body-tertiary border-0 px-4" placeholder="Symbol 2">
                </div>
                <div class="col-md-4">
                    <button id="compareBtn" class="btn btn-primary rounded-pill w-100 fw-semibold shadow-sm">Compare Stocks</button>
                </div>
            </div>
        </div>
    </div>

    <div id="compareResults" class="d-none">
        <div class="row g-4 mb-4">
            <div class="col-md-6" id="stock1Card"></div>
            <div class="col-md-6" id="stock2Card"></div>
        </div>
        <div class="card border-0 bg-gradient-dark text-white rounded-4 shadow-sm premium-card">
            <div class="card-body p-4 p-md-5">
                <h5 class="fw-bold tracking-tight text-white mb-4"><i class="fa-solid fa-sparkles text-warning me-2"></i> AI Comparison Summary</h5>
                <div id="aiSummary" class="markdown-body text-white opacity-90 lh-lg">
                    <div class="spinner-grow spinner-grow-sm text-warning" role="status"></div> Analyzing comparison...
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
document.getElementById('compareBtn').addEventListener('click', async () => {
    const s1 = document.getElementById('sym1').value.toUpperCase();
    const s2 = document.getElementById('sym2').value.toUpperCase();
    if(!s1 || !s2) return alert('Enter two symbols');
    
    document.getElementById('compareResults').classList.remove('d-none');
    document.getElementById('stock1Card').innerHTML = '<div class="spinner-border text-primary"></div>';
    document.getElementById('stock2Card').innerHTML = '<div class="spinner-border text-primary"></div>';
    
    const fetchStock = async (sym, elemId) => {
        try {
            const res = await fetch(`/api/stock/search?q=${sym}`);
            const data = await res.json();
            if(data.error) throw new Error(data.error);
            const html = `
                <div class="card border-0 shadow-sm rounded-4 bg-body h-100">
                    <div class="card-body p-4">
                        <h4 class="fw-bold">${data.name} (${data.symbol})</h4>
                        <h2 class="display-5 fw-bold mb-0">${data.price} <span class="fs-6 text-muted">${data.currency}</span></h2>
                        <p class="${data.change >= 0 ? 'text-success' : 'text-danger'} fw-medium">${data.change_percent}%</p>
                        <ul class="list-group list-group-flush mt-4">
                            <li class="list-group-item bg-transparent d-flex justify-content-between px-0"><span>Market Cap</span> <strong>${data.market_cap}</strong></li>
                            <li class="list-group-item bg-transparent d-flex justify-content-between px-0"><span>Volume</span> <strong>${data.volume}</strong></li>
                        </ul>
                    </div>
                </div>`;
            document.getElementById(elemId).innerHTML = html;
            return data;
        } catch(e) {
            document.getElementById(elemId).innerHTML = `<div class="alert alert-danger border-0">Failed to load ${sym}</div>`;
            return null;
        }
    };

    const [d1, d2] = await Promise.all([fetchStock(s1, 'stock1Card'), fetchStock(s2, 'stock2Card')]);
    
    if(d1 && d2) {
        document.getElementById('aiSummary').innerHTML = '<div class="spinner-grow spinner-grow-sm text-warning" role="status"></div> Analyzing comparison...';
        const query = `Compare ${d1.name} (${d1.symbol}) and ${d2.name} (${d2.symbol}). ${d1.symbol} price: ${d1.price}, ${d2.symbol} price: ${d2.price}. Provide a brief professional comparison of their market position.`;
        fetch('/api/agent/ask', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
            body: JSON.stringify({query: query, history: []})
        }).then(res => res.json()).then(data => {
            const parsed = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response;
            document.getElementById('aiSummary').innerHTML = parsed;
        });
    }
});
</script>
{% endblock %}
""",
    
    'alerts.html': """{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-0">
    <h2 class="fw-bold tracking-tight mb-4">Price Alerts</h2>
    <div class="row g-4">
        <div class="col-md-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card">
                <div class="card-body p-4">
                    <h5 class="fw-bold mb-3">Create Alert</h5>
                    <div class="mb-3">
                        <label class="form-label text-muted fw-medium">Symbol</label>
                        <input type="text" id="alertSymbol" class="form-control rounded-pill bg-body-tertiary border-0 px-4" placeholder="e.g. AAPL">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted fw-medium">Condition</label>
                        <select id="alertCondition" class="form-select rounded-pill bg-body-tertiary border-0 px-4">
                            <option value="above">Goes Above</option>
                            <option value="below">Goes Below</option>
                        </select>
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted fw-medium">Target Price</label>
                        <input type="number" id="alertPrice" class="form-control rounded-pill bg-body-tertiary border-0 px-4" placeholder="0.00">
                    </div>
                    <button id="saveAlertBtn" class="btn btn-primary rounded-pill w-100 fw-semibold shadow-sm">Save Alert</button>
                </div>
            </div>
        </div>
        <div class="col-md-8">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100">
                <div class="card-body p-4">
                    <h5 class="fw-bold mb-4">Active Alerts</h5>
                    <div id="alertsList" class="text-center text-muted py-5">
                        <i class="fa-regular fa-bell fa-3x mb-3 text-secondary opacity-50"></i>
                        <p>Loading alerts...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
    function loadAlerts() {
        fetch('/api/alerts')
            .then(res => res.json())
            .then(data => {
                const list = document.getElementById('alertsList');
                if(!data.length) {
                    list.innerHTML = '<i class="fa-regular fa-bell fa-3x mb-3 text-secondary opacity-50"></i><p>No active alerts.</p>';
                    return;
                }
                let html = '<ul class="list-group list-group-flush text-start">';
                data.forEach(a => {
                    html += `
                    <li class="list-group-item bg-transparent d-flex justify-content-between align-items-center py-3 px-0 border-bottom">
                        <div>
                            <h6 class="fw-bold mb-1">${a.symbol}</h6>
                            <small class="text-muted">Target: ${a.condition} ${a.target_price}</small>
                        </div>
                        <button class="btn btn-sm btn-outline-danger rounded-pill px-3" onclick="deleteAlert(${a.id})">Delete</button>
                    </li>`;
                });
                html += '</ul>';
                list.innerHTML = html;
            });
    }

    document.getElementById('saveAlertBtn').addEventListener('click', () => {
        const payload = {
            symbol: document.getElementById('alertSymbol').value.toUpperCase(),
            condition: document.getElementById('alertCondition').value,
            target_price: parseFloat(document.getElementById('alertPrice').value)
        };
        fetch('/api/alerts', {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(() => {
            document.getElementById('alertSymbol').value = '';
            document.getElementById('alertPrice').value = '';
            loadAlerts();
        });
    });

    function deleteAlert(id) {
        fetch(`/api/alerts/${id}`, {
            method: 'DELETE',
            headers: {'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')}
        }).then(() => loadAlerts());
    }

    document.addEventListener('DOMContentLoaded', loadAlerts);
</script>
{% endblock %}
""",

    'academy.html': """{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-0">
    <div class="text-center mb-5">
        <h1 class="fw-bold tracking-tight display-5 mb-3">Finance Academy</h1>
        <p class="lead text-muted max-w-700 mx-auto">Master the fundamentals of investing with our easy-to-understand glossary of financial terms.</p>
    </div>
    
    <div class="row g-4">
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-primary-subtle text-primary rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-chart-pie"></i></div>
                    <h5 class="fw-bold">Market Capitalization</h5>
                    <p class="text-muted small">The total market value of a company's outstanding shares. It's calculated by multiplying the current stock price by the total number of outstanding shares.</p>
                </div>
            </div>
        </div>
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-success-subtle text-success rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-divide"></i></div>
                    <h5 class="fw-bold">P/E Ratio (Price-to-Earnings)</h5>
                    <p class="text-muted small">A valuation ratio comparing a company's current share price to its per-share earnings. A high P/E might mean a stock is overvalued or investors expect high growth.</p>
                </div>
            </div>
        </div>
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-info-subtle text-info rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-coins"></i></div>
                    <h5 class="fw-bold">EPS (Earnings Per Share)</h5>
                    <p class="text-muted small">A company's net profit divided by the number of common shares it has outstanding. EPS indicates how much money a company makes for each share of its stock.</p>
                </div>
            </div>
        </div>
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-warning-subtle text-warning rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-arrow-trend-up"></i></div>
                    <h5 class="fw-bold">CAGR</h5>
                    <p class="text-muted small">Compound Annual Growth Rate is the mean annual growth rate of an investment over a specified period of time longer than one year.</p>
                </div>
            </div>
        </div>
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-danger-subtle text-danger rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-bullhorn"></i></div>
                    <h5 class="fw-bold">Bull & Bear Markets</h5>
                    <p class="text-muted small">A Bull market is when the economy is doing well and stock prices are rising. A Bear market is when the economy is bad and prices are falling.</p>
                </div>
            </div>
        </div>
        <div class="col-md-6 col-lg-4">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100 p-3">
                <div class="card-body">
                    <div class="bg-secondary-subtle text-secondary rounded-circle d-flex align-items-center justify-content-center mb-3" style="width: 48px; height: 48px;"><i class="fa-solid fa-money-bill-wave"></i></div>
                    <h5 class="fw-bold">Dividend</h5>
                    <p class="text-muted small">A distribution of a portion of a company's earnings, decided by the board of directors, paid to a class of its shareholders.</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
""",

    'tools.html': """{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-0">
    <h2 class="fw-bold tracking-tight mb-4">Financial Calculators</h2>
    <div class="row g-4">
        <!-- SIP Calculator -->
        <div class="col-md-6">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100">
                <div class="card-body p-4">
                    <h5 class="fw-bold mb-4"><i class="fa-solid fa-calculator text-primary me-2"></i> SIP Calculator</h5>
                    <div class="mb-3">
                        <label class="form-label text-muted small">Monthly Investment</label>
                        <input type="number" id="sipAmount" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="5000">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted small">Expected Return Rate (p.a %)</label>
                        <input type="number" id="sipRate" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="12">
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted small">Time Period (Years)</label>
                        <input type="number" id="sipYears" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="10">
                    </div>
                    <button class="btn btn-primary rounded-pill w-100 fw-medium shadow-sm mb-4" onclick="calculateSIP()">Calculate</button>
                    
                    <div class="p-3 bg-primary-subtle text-primary-emphasis rounded-4 text-center">
                        <p class="mb-1 small">Estimated Returns</p>
                        <h3 class="fw-bold mb-0" id="sipResult">0.00</h3>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- CAGR Calculator -->
        <div class="col-md-6">
            <div class="card border-0 shadow-sm rounded-4 premium-card h-100">
                <div class="card-body p-4">
                    <h5 class="fw-bold mb-4"><i class="fa-solid fa-arrow-trend-up text-success me-2"></i> CAGR Calculator</h5>
                    <div class="mb-3">
                        <label class="form-label text-muted small">Initial Value</label>
                        <input type="number" id="cagrInitial" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="10000">
                    </div>
                    <div class="mb-3">
                        <label class="form-label text-muted small">Final Value</label>
                        <input type="number" id="cagrFinal" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="20000">
                    </div>
                    <div class="mb-4">
                        <label class="form-label text-muted small">Duration (Years)</label>
                        <input type="number" id="cagrYears" class="form-control bg-body-tertiary border-0 rounded-pill px-3" value="5">
                    </div>
                    <button class="btn btn-success rounded-pill w-100 fw-medium shadow-sm mb-4" onclick="calculateCAGR()">Calculate</button>
                    
                    <div class="p-3 bg-success-subtle text-success-emphasis rounded-4 text-center">
                        <p class="mb-1 small">CAGR</p>
                        <h3 class="fw-bold mb-0" id="cagrResult">0.00%</h3>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function calculateSIP() {
    const P = parseFloat(document.getElementById('sipAmount').value);
    const i = parseFloat(document.getElementById('sipRate').value) / 100 / 12;
    const n = parseFloat(document.getElementById('sipYears').value) * 12;
    
    if(P && i && n) {
        const M = P * ((Math.pow(1 + i, n) - 1) / i) * (1 + i);
        document.getElementById('sipResult').textContent = M.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits:2});
    }
}
function calculateCAGR() {
    const start = parseFloat(document.getElementById('cagrInitial').value);
    const end = parseFloat(document.getElementById('cagrFinal').value);
    const years = parseFloat(document.getElementById('cagrYears').value);
    
    if(start && end && years) {
        const cagr = (Math.pow(end/start, 1/years) - 1) * 100;
        document.getElementById('cagrResult').textContent = cagr.toFixed(2) + '%';
    }
}
</script>
{% endblock %}
""",

    'reports.html': """{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-0">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold tracking-tight mb-0">Financial Reports</h2>
        <button class="btn btn-primary rounded-pill px-4 fw-medium shadow-sm" onclick="window.print()"><i class="fa-solid fa-print me-2"></i> Print Report</button>
    </div>
    
    <div class="card border-0 shadow-sm rounded-4 premium-card mb-4">
        <div class="card-body p-5">
            <div class="text-center mb-5">
                <h3 class="fw-bold">Portfolio Summary Report</h3>
                <p class="text-muted">Generated on <span id="reportDate"></span></p>
            </div>
            
            <div class="row mb-5">
                <div class="col-md-4 text-center">
                    <p class="text-muted small mb-1">Total Value</p>
                    <h4 class="fw-bold" id="repValue">--</h4>
                </div>
                <div class="col-md-4 text-center">
                    <p class="text-muted small mb-1">Total Cost</p>
                    <h4 class="fw-bold" id="repCost">--</h4>
                </div>
                <div class="col-md-4 text-center">
                    <p class="text-muted small mb-1">Unrealized P/L</p>
                    <h4 class="fw-bold" id="repPL">--</h4>
                </div>
            </div>
            
            <h5 class="fw-bold mb-3">Holdings Breakdown</h5>
            <div class="table-responsive">
                <table class="table table-borderless align-middle">
                    <thead class="border-bottom">
                        <tr class="text-muted small">
                            <th>Symbol</th>
                            <th>Qty</th>
                            <th>Cost Basis</th>
                            <th>Current Value</th>
                        </tr>
                    </thead>
                    <tbody id="repHoldings">
                        <tr><td colspan="4" class="text-center py-4">Loading report data...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
{% block scripts %}
<script>
document.getElementById('reportDate').textContent = new Date().toLocaleDateString();
fetch('/api/portfolio')
    .then(res => res.json())
    .then(data => {
        let totalVal = 0, totalCost = 0, html = '';
        if(data.length === 0) {
            document.getElementById('repHoldings').innerHTML = '<tr><td colspan="4" class="text-center text-muted">No holdings in portfolio.</td></tr>';
            return;
        }
        data.forEach(item => {
            totalVal += item.current_value;
            totalCost += item.total_cost;
            html += `<tr>
                <td class="fw-bold">${item.symbol}</td>
                <td>${item.quantity}</td>
                <td>${item.purchase_price.toFixed(2)}</td>
                <td>${item.current_value.toFixed(2)}</td>
            </tr>`;
        });
        document.getElementById('repValue').textContent = totalVal.toFixed(2);
        document.getElementById('repCost').textContent = totalCost.toFixed(2);
        
        const pl = totalVal - totalCost;
        const plElem = document.getElementById('repPL');
        plElem.textContent = pl.toFixed(2);
        plElem.className = 'fw-bold ' + (pl >= 0 ? 'text-success' : 'text-danger');
        
        document.getElementById('repHoldings').innerHTML = html;
    });
</script>
{% endblock %}
"""
}

for name, content in templates.items():
    path = os.path.join('app/templates', name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
print("Created templates successfully.")
