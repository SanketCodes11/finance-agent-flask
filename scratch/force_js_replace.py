import re

file_path = 'app/templates/stock_detail.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace scripts
start_script_idx = content.find('<script>')
if start_script_idx != -1:
    end_script_idx = content.find('</script>', start_script_idx) + 9
    old_script_block = content[start_script_idx:end_script_idx]
    
    new_script_block = '''<script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
<script src="{{ url_for('static', filename='js/indicators.js') }}"></script>
<script src="{{ url_for('static', filename='js/tv_chart.js') }}"></script>
<script>
    const SYMBOL = '{{ symbol }}';
    let tvChartMgr = null;
    let currentChartType = 'candle';
    let rawChartData = null;
    let isWatchlisted = {{ 'true' if is_watchlisted else 'false' }};
    let companyName = SYMBOL;

    document.addEventListener('DOMContentLoaded', function() {
        fetchStockData();
        fetchChartData('1mo');

        document.getElementById('refreshBtn').addEventListener('click', () => {
            fetchStockData();
            const activeRange = document.querySelector('.range-btn.active')?.dataset.range || '1mo';
            fetchChartData(activeRange);
        });

        // Range buttons
        document.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.range-btn').forEach(b => {
                    b.classList.remove('bg-primary', 'text-white', 'shadow-sm', 'active');
                    b.classList.add('text-muted');
                });
                this.classList.remove('text-muted');
                this.classList.add('bg-primary', 'text-white', 'shadow-sm', 'active');
                fetchChartData(this.dataset.range);
            });
        });

        // Watchlist Button
        document.getElementById('watchlistBtn').addEventListener('click', function() {
            const btn = this;
            btn.disabled = true;
            
            fetch('/api/watchlist', {
                method: isWatchlisted ? 'DELETE' : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
                },
                body: JSON.stringify({ symbol: SYMBOL })
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    isWatchlisted = !isWatchlisted;
                    if (isWatchlisted) {
                        btn.classList.remove('btn-outline-primary', 'bg-body');
                        btn.classList.add('btn-primary');
                        btn.innerHTML = '<i class="fa-solid fa-star me-2"></i><span id="watchlistText">In Watchlist</span>';
                    } else {
                        btn.classList.remove('btn-primary');
                        btn.classList.add('btn-outline-primary', 'bg-body');
                        btn.innerHTML = '<i class="fa-regular fa-star me-2"></i><span id="watchlistText">Add to Watchlist</span>';
                    }
                }
            }).finally(() => { btn.disabled = false; });
        });
        
        // Indicator toggles
        document.querySelectorAll('.ind-toggle').forEach(cb => {
            cb.addEventListener('change', applyActiveIndicators);
        });

        // Chart Type toggles
        document.querySelectorAll('.chart-type-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                document.querySelectorAll('.chart-type-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentChartType = this.dataset.type;
                document.getElementById('chartTypeLabel').textContent = this.dataset.label;
                
                if (tvChartMgr && rawChartData) {
                    tvChartMgr.setData(rawChartData, currentChartType);
                    applyActiveIndicators();
                }
            });
        });
        
        document.getElementById('bd-theme').addEventListener('click', () => {
            if (tvChartMgr) {
                setTimeout(() => {
                    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark' || (document.documentElement.getAttribute('data-bs-theme') === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                    tvChartMgr.setTheme(isDark);
                }, 100);
            }
        });
    });

    function formatNumber(num) {
        if (!num) return '--';
        if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        return num.toLocaleString();
    }

    function fetchStockData() {
        const errorContainer = document.getElementById('errorContainer');
        const mainContent = document.getElementById('mainContent');
        
        fetch(`/api/stock/search?q=${SYMBOL}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) throw new Error(data.error);
                
                errorContainer.classList.add('d-none');
                mainContent.style.opacity = '1';
                companyName = data.name || SYMBOL;
                
                document.getElementById('stockName').innerHTML = companyName;
                
                if (data.exchange && data.exchange !== 'Unknown Exchange') {
                    const exElem = document.getElementById('stockExchange');
                    exElem.textContent = data.exchange;
                    exElem.classList.remove('d-none');
                }
                
                const priceElem = document.getElementById('stockPrice');
                priceElem.textContent = data.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                document.getElementById('stockCurrency').textContent = data.currency;
                
                const changeElem = document.getElementById('stockChange');
                const changePercentElem = document.getElementById('stockChangePercent');
                const isPos = data.change >= 0;
                const sign = isPos ? '+' : '';
                
                changeElem.textContent = sign + data.change.toFixed(2);
                changePercentElem.innerHTML = `<i class="fa-solid fa-arrow-${isPos ? 'trend-up' : 'trend-down'} me-1"></i> ${sign}${data.change_percent.toFixed(2)}%`;
                
                changeElem.className = isPos ? 'text-success fw-bold me-3 fs-4 tracking-tight' : 'text-danger fw-bold me-3 fs-4 tracking-tight';
                changePercentElem.className = isPos ? 'badge bg-success-subtle text-success fs-6 px-3 py-2 rounded-pill' : 'badge bg-danger-subtle text-danger fs-6 px-3 py-2 rounded-pill';
                
                document.getElementById('statPrevClose').textContent = data.previousClose ? data.previousClose.toFixed(2) : '--';
                document.getElementById('statOpen').textContent = data.open ? data.open.toFixed(2) : '--';
                document.getElementById('statRange').textContent = (data.dayLow && data.dayHigh) ? `${data.dayLow.toFixed(2)} - ${data.dayHigh.toFixed(2)}` : '--';
                document.getElementById('stat52High').textContent = data.fiftyTwoWeekHigh ? data.fiftyTwoWeekHigh.toFixed(2) : '--';
                document.getElementById('stat52Low').textContent = data.fiftyTwoWeekLow ? data.fiftyTwoWeekLow.toFixed(2) : '--';
                document.getElementById('statVolume').textContent = formatNumber(data.volume);
                document.getElementById('statMarketCap').textContent = formatNumber(data.market_cap);
                
                generateAIAnalysis(companyName, data);
                loadStockNews(companyName);
            })
            .catch(err => {
                errorContainer.classList.remove('d-none');
                mainContent.style.opacity = '0.5';
            });
    }

    function generateAIAnalysis(name, stockData) {
        const container = document.getElementById('aiAnalysisContainer');
        const query = `Analyze the stock ${name} (${SYMBOL}). Current Price: ${stockData.price}, 52W Range: ${stockData.fiftyTwoWeekLow}-${stockData.fiftyTwoWeekHigh}, Market Cap: ${formatNumber(stockData.market_cap)}. Keep the analysis highly concise, structured with short bullet points, professional, and focus on general market positioning. Do not give financial advice.`;
        
        fetch('/api/agent/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content') },
            body: JSON.stringify({ query: query, history: [] })
        }).then(res => res.json()).then(data => {
            if (data.error) {
                container.innerHTML = `<div class="text-white-50"><i class="fa-solid fa-triangle-exclamation me-2"></i> ${data.error}</div>`;
            } else {
                const parsedMarkdown = typeof marked !== 'undefined' ? marked.parse(data.response) : data.response.replace(/\\n/g, '<br>');
                container.innerHTML = parsedMarkdown;
            }
        }).catch(err => {
            container.innerHTML = `<div class="text-white-50"><i class="fa-solid fa-circle-exclamation me-2"></i> AI Analysis is currently unavailable.</div>`;
        });
    }

    function loadStockNews(query) {
        const container = document.getElementById('stockNewsContainer');
        fetch(`/api/news?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                container.innerHTML = '';
                const articles = data.articles || [];
                
                if (articles.length === 0) {
                    container.innerHTML = '<div class="col-12"><div class="card bg-body text-center py-5 border-0 rounded-4 text-muted">No related news found.</div></div>';
                    return;
                }
                
                articles.slice(0, 3).forEach(article => {
                    const date = new Date(article.publishedAt).toLocaleDateString(undefined, {month:'short', day:'numeric'});
                    const img = article.urlToImage ? `<img src="${article.urlToImage}" class="card-img-top news-img-modern" alt="News Image" onerror="this.src='https://via.placeholder.com/400x200?text=No+Image'">` : `<div class="bg-secondary-subtle d-flex align-items-center justify-content-center news-img-modern"><i class="fa-regular fa-image fa-2x text-secondary"></i></div>`;
                    
                    const html = `
                        <div class="col-md-6 col-lg-4">
                            <div class="card h-100 border-0 bg-body shadow-sm rounded-4 premium-card d-flex flex-column">
                                ${img}
                                <div class="card-body p-4 d-flex flex-column">
                                    <div class="d-flex justify-content-between align-items-center mb-3">
                                        <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1 rounded-pill">${article.source}</span>
                                        <small class="text-muted fw-medium">${date}</small>
                                    </div>
                                    <h5 class="card-title text-body fs-6 fw-bold mb-3 tracking-tight lh-base">${article.title}</h5>
                                    <p class="card-text text-muted small flex-grow-1">${article.description ? article.description.substring(0, 80) + '...' : ''}</p>
                                    <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="text-primary text-decoration-none mt-auto fw-semibold small">Read Article <i class="fa-solid fa-arrow-right ms-1"></i></a>
                                </div>
                            </div>
                        </div>`;
                    container.innerHTML += html;
                });
            })
            .catch(err => {
                container.innerHTML = `<div class="col-12"><div class="alert bg-danger-subtle text-danger border-0 rounded-4 shadow-sm"><i class="fa-solid fa-circle-exclamation me-2"></i> Failed to load related news.</div></div>`;
            });
    }

    function fetchChartData(period) {
        const loading = document.getElementById('chartLoading');
        if(loading) loading.classList.remove('d-none');
        
        fetch(`/api/stock/history?symbol=${SYMBOL}&period=${period}`)
            .then(res => res.json())
            .then(data => {
                if(loading) loading.classList.add('d-none');
                if (data.error) return;
                
                // Format for Lightweight Charts
                const formattedData = [];
                for(let i=0; i<data.timestamps.length; i++) {
                    formattedData.push({
                        time: data.timestamps[i],
                        open: data.open[i],
                        high: data.high[i],
                        low: data.low[i],
                        close: data.close[i],
                        volume: data.volume[i]
                    });
                }
                
                // Sort ascending
                formattedData.sort((a,b) => a.time - b.time);
                rawChartData = formattedData;
                
                const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark' || (document.documentElement.getAttribute('data-bs-theme') === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                
                if (!tvChartMgr) {
                    tvChartMgr = new TVChart('tvChart', isDark);
                } else {
                    tvChartMgr.setTheme(isDark);
                }
                
                tvChartMgr.setData(formattedData, currentChartType);
                applyActiveIndicators();
            })
            .catch(err => { 
                if(loading) loading.classList.add('d-none'); 
                console.error('Failed to load chart data:', err); 
            });
    }

    function applyActiveIndicators() {
        if (!tvChartMgr) return;
        tvChartMgr.clearIndicators();
        document.querySelectorAll('.ind-toggle:checked').forEach(cb => {
            const ind = cb.dataset.ind;
            const params = {};
            if (cb.dataset.period) params.period = parseInt(cb.dataset.period);
            if (cb.dataset.dev) params.stdDev = parseFloat(cb.dataset.dev);
            if (cb.dataset.fast) params.fast = parseInt(cb.dataset.fast);
            if (cb.dataset.slow) params.slow = parseInt(cb.dataset.slow);
            if (cb.dataset.signal) params.signal = parseInt(cb.dataset.signal);
            tvChartMgr.addIndicator(ind, params);
        });
    }
</script>'''
    content = content.replace(old_script_block, new_script_block)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced entire JS block successfully.")
else:
    print("Could not find <script> tag.")
