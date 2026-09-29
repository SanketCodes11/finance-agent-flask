import os

with open('app/templates/portfolio.html', 'r', encoding='utf-8') as f:
    content = f.read()

historical_html = """
<div class="row mb-4">
    <div class="col-12">
        <div class="card border-0 bg-body rounded-4 shadow-sm">
            <div class="card-header bg-transparent border-0 pt-4 pb-0 px-4 d-flex justify-content-between align-items-center flex-wrap gap-2">
                <h5 class="fw-bold tracking-tight mb-0">Historical Performance <span class="badge bg-primary-subtle text-primary ms-2 fs-6">Beta</span></h5>
                <div class="btn-group" role="group" id="histBtnGroup">
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="loadHistorical('1M')">1M</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="loadHistorical('3M')">3M</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="loadHistorical('6M')">6M</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary active" onclick="loadHistorical('1Y')">1Y</button>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="loadHistorical('ALL')">ALL</button>
                </div>
            </div>
            <div class="card-body p-4 pt-3">
                <div id="historicalLoading" class="text-center py-5 d-none">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="text-muted mt-3 small">Reconstructing portfolio ledger...</p>
                </div>
                <div id="historicalError" class="alert alert-danger d-none small"></div>
                
                <div id="historicalChartContainer" style="height: 300px; position: relative;">
                    <canvas id="historicalChart"></canvas>
                </div>
                
                <div class="row text-center mt-3 pt-3 border-top" id="historicalMetrics">
                    <div class="col">
                        <span class="d-block text-muted small fw-medium text-uppercase tracking-wide">Return</span>
                        <span class="fw-bold" id="histAbsReturn">--</span>
                    </div>
                    <div class="col border-start">
                        <span class="d-block text-muted small fw-medium text-uppercase tracking-wide">Performance</span>
                        <span class="fw-bold" id="histPctReturn">--</span>
                    </div>
                    <div class="col border-start">
                        <span class="d-block text-muted small fw-medium text-uppercase tracking-wide">Peak Value</span>
                        <span class="fw-bold" id="histPeak">--</span>
                    </div>
                    <div class="col border-start">
                        <span class="d-block text-muted small fw-medium text-uppercase tracking-wide">Max Drawdown</span>
                        <span class="fw-bold text-danger" id="histDrawdown">--</span>
                    </div>
                </div>
                <div class="text-muted small mt-3 px-2 text-center fst-italic">
                    <i class="fa-solid fa-circle-info me-1"></i>
                    Performance reconstructed from your recorded transaction ledger. Legacy holdings without explicit BUY transactions are excluded. Excludes broker fees/taxes. 
                </div>
            </div>
        </div>
    </div>
</div>
"""

js_code = """
    let historicalChartInstance = null;
    let currentPeriod = '1Y';

    function loadHistorical(period) {
        currentPeriod = period;
        
        // Update active button
        const buttons = document.getElementById('histBtnGroup').querySelectorAll('button');
        buttons.forEach(btn => btn.classList.remove('active'));
        const activeBtn = Array.from(buttons).find(btn => btn.textContent === period);
        if (activeBtn) activeBtn.classList.add('active');

        document.getElementById('historicalLoading').classList.remove('d-none');
        document.getElementById('historicalError').classList.add('d-none');
        document.getElementById('historicalChartContainer').classList.add('d-none');
        document.getElementById('historicalMetrics').classList.add('d-none');

        fetch(`/api/portfolio/historical?period=${period}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to load historical data');
                return res.json();
            })
            .then(data => {
                if (data.error) throw new Error(data.error);
                renderHistoricalChart(data);
            })
            .catch(err => {
                const errElem = document.getElementById('historicalError');
                errElem.textContent = err.message;
                errElem.classList.remove('d-none');
            })
            .finally(() => {
                document.getElementById('historicalLoading').classList.add('d-none');
            });
    }

    function renderHistoricalChart(data) {
        if (!data.labels || data.labels.length === 0) {
            const errElem = document.getElementById('historicalError');
            errElem.innerHTML = '<strong>No historical data available.</strong><br>Ensure you have added complete BUY/SELL transactions to your portfolio ledger to enable reconstruction.';
            errElem.classList.remove('d-none');
            errElem.classList.replace('alert-danger', 'alert-info');
            return;
        }

        document.getElementById('historicalError').classList.add('d-none');
        document.getElementById('historicalChartContainer').classList.remove('d-none');
        document.getElementById('historicalMetrics').classList.remove('d-none');

        // Update metrics
        const m = data.metrics;
        const absReturnElem = document.getElementById('histAbsReturn');
        const pctReturnElem = document.getElementById('histPctReturn');
        
        absReturnElem.textContent = `${m.absolute_return >= 0 ? '+' : ''}$${m.absolute_return.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        absReturnElem.className = `fw-bold ${m.absolute_return >= 0 ? 'text-success' : 'text-danger'}`;
        
        pctReturnElem.textContent = `${m.percentage_return >= 0 ? '+' : ''}${m.percentage_return.toFixed(2)}%`;
        pctReturnElem.className = `fw-bold ${m.percentage_return >= 0 ? 'text-success' : 'text-danger'}`;
        
        document.getElementById('histPeak').textContent = '$' + m.peak_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById('histDrawdown').textContent = m.max_drawdown > 0 ? `-${m.max_drawdown.toFixed(2)}%` : '--';

        const ctx = document.getElementById('historicalChart').getContext('2d');
        if (historicalChartInstance) {
            historicalChartInstance.destroy();
        }

        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark' || (document.documentElement.getAttribute('data-bs-theme') === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)';
        const textColor = isDark ? '#adb5bd' : '#6c757d';

        historicalChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: 'Market Value',
                        data: data.market_values,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.1
                    },
                    {
                        label: 'Invested Capital',
                        data: data.invested_capital,
                        borderColor: '#198754',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: textColor }
                    },
                    tooltip: {
                        backgroundColor: isDark ? 'rgba(33, 37, 41, 0.95)' : 'rgba(255, 255, 255, 0.95)',
                        titleColor: isDark ? '#adb5bd' : '#6c757d',
                        bodyColor: isDark ? '#f8f9fa' : '#212529',
                        borderColor: isDark ? '#495057' : '#dee2e6',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: {
                            color: textColor,
                            maxTicksLimit: 6,
                            callback: function(value, index, values) {
                                const dateStr = data.labels[index];
                                if (!dateStr) return '';
                                const d = new Date(dateStr);
                                return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: '2-digit' });
                            }
                        }
                    },
                    y: {
                        grid: { color: gridColor, drawBorder: false },
                        ticks: {
                            color: textColor,
                            callback: function(value) {
                                if (value >= 1000000) return '$' + (value / 1000000).toFixed(1) + 'M';
                                if (value >= 1000) return '$' + (value / 1000).toFixed(1) + 'k';
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    // Initialize historical chart
    document.addEventListener('DOMContentLoaded', () => {
        loadHistorical('1Y');
    });
"""

if "id=\"historicalChart\"" not in content:
    content = content.replace('<div class="row g-4">', historical_html + '\n<div class="row g-4">')
    
    # Inject JS just before the closing script tag or at end of block
    content = content.replace('// Make functions global for inline onclick', js_code + '\n    // Make functions global for inline onclick')
    
    with open('app/templates/portfolio.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected UI components into portfolio.html")
else:
    print("UI components already injected")
